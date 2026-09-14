"""Authorization Engine — the module's single authorization chokepoint.

# [TR017/SP017] `resolve(actor, target, action) -> AuthzContext` is the only
# sanctioned way any component learns what an actor may do, and the only place
# `mangaly.authz_context` is ever set.
# Approach: SP017 names this the highest-blast-radius item in the module, and
# the two failure modes it names are configuration failures, not logic ones —
# a table-owning connection, and a plain `SET` leaking context across pooled
# connections. So `resolve()` is built so neither is expressible here:
#   * it sets the session variable through `db.session.set_authz_context()`,
#     which hardcodes `set_config(..., is_local => true)` and refuses to run
#     outside a transaction (there is no code path that emits a plain `SET`);
#   * it re-resolves on every request rather than caching a decision, matching
#     SP010's "Class A, every request re-resolves, not cached" threshold — a
#     cached grant would survive its own revocation, which is exactly what
#     TR010's immediate-revocation requirement forbids;
#   * the grant read is a single indexed query against
#     `idx_grant_target(target_profile_id, scope, status)`, so the chokepoint
#     cannot become the DoS bottleneck SP017's denial-of-service row names.
#
# [TR018/SP018] The two scopes are read as two independently-typed grant rows,
# never a combined boolean — `scopes` is a `frozenset[GrantScope]`.
#
# [TR069/SP069] Every resolution publishes its decision to
# `mangaly_authz.outbox_event` in the same transaction, so a grant/deny is
# reconstructable afterwards.
# Traces to: TR017, TR018, TR010, TR069, SP017, SP018, SP069,
#            MODULE-ARCHITECTURE-STANDARD §5, CODING-GUIDE.md §3.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.components.authorization.context import (
    Action,
    AuthorizationDenied,
    AuthzContext,
    Capacity,
    GrantScope,
    GrantType,
)
from app.components.authorization.models import Grant
from app.db.session import set_authz_context
from app.events import bus
from app.events.dto import audit_payload

logger = logging.getLogger(__name__)

_SCHEMA = "mangaly_authz"

# Only `active` grants count. `withheld` (TR011's disputed-relationship state)
# and `revoked` (TR010's removal state) are both non-granting, and are read here
# as "not active" rather than being enumerated — so a future fourth status
# defaults to denying rather than to granting.
_ACTIVE_GRANTS_SQL = text(
    """
    SELECT scope::text AS scope, grant_type::text AS grant_type
    FROM mangaly_authz.grant
    WHERE subject_id = :subject_id
      AND target_profile_id = :target_profile_id
      AND status = 'active'
    """
)


async def resolve(
    session: AsyncSession,
    *,
    subject_id: UUID,
    account_id: UUID,
    target_profile_id: UUID | None,
    action: Action,
    capacity: Capacity = Capacity.CANDIDATE,
    publish_decision: bool = True,
) -> AuthzContext:
    """Resolve the BR04 chain for one actor/target/action and bind it to this transaction.

    Must be called inside an open transaction: the `SET LOCAL` it performs is
    transaction-scoped, so the transaction boundary IS the authorization
    boundary.
    """
    if not session.in_transaction():
        raise AuthorizationDenied(
            "resolve() requires an open transaction — the authorization context "
            "it sets is transaction-local by design (TR017/SP017)."
        )

    # Step 1: bind the context BEFORE reading grants. The grant table's own RLS
    # policy (`grant_visible_to_subject_or_target`) keys on this variable, so
    # reading grants without it set correctly returns nothing.
    await set_authz_context(session, subject_id)

    # Step 2: self-access. A candidate acting on their own profile needs no
    # grant row; `mangaly_authz.is_self()` encodes the same rule in every RLS
    # predicate, and this mirrors it rather than inventing a second rule.
    is_self = target_profile_id is None or await _is_self(session, target_profile_id)

    # Step 3: the grant chain.
    scopes: set[GrantScope] = set()
    grant_basis: dict[str, str] = {}
    if target_profile_id is not None and not is_self:
        rows = await session.execute(
            _ACTIVE_GRANTS_SQL,
            {"subject_id": str(subject_id), "target_profile_id": str(target_profile_id)},
        )
        for row in rows.mappings():
            scope = GrantScope(row["scope"])
            scopes.add(scope)
            grant_basis[scope.value] = row["grant_type"]

    context = AuthzContext(
        subject_id=subject_id,
        account_id=account_id,
        target_profile_id=target_profile_id,
        action=action,
        capacity=capacity,
        scopes=frozenset(scopes),
        resolved_at=datetime.now(UTC),
        grant_basis=grant_basis,
        is_self=is_self,
    )

    if publish_decision:
        # [TR069/SP069] Same transaction as the resolution it records.
        await bus.publish(
            session,
            schema=_SCHEMA,
            aggregate_id=target_profile_id or subject_id,
            event_type="authz.resolved",
            payload=audit_payload(context),
        )

    logger.debug(
        "authz resolved subject=%s target=%s self=%s scopes=%s",
        subject_id,
        target_profile_id,
        is_self,
        sorted(s.value for s in scopes),
    )
    return context


async def _is_self(session: AsyncSession, target_profile_id: UUID) -> bool:
    """Delegate the self-check to the same DB function every RLS policy calls.

    Deliberately not reimplemented in Python: `mangaly_authz.is_self()` is what
    the policies enforce, so evaluating a *different* rule in the application
    would let the two drift — the same divergence class TR003/TR027 already had
    to correct once.
    """
    result = await session.execute(
        text("SELECT mangaly_authz.is_self(CAST(:target AS uuid))"),
        {"target": str(target_profile_id)},
    )
    return bool(result.scalar_one())


async def resolve_self(
    session: AsyncSession,
    *,
    account_id: UUID,
    action: Action,
    capacity: Capacity = Capacity.CANDIDATE,
) -> AuthzContext:
    """Resolve a self-scoped context (an actor operating on their own data).

    Provided so a self-only endpoint (profile create, settings) still goes
    through the chokepoint and still binds `mangaly.authz_context`, rather than
    "skipping authorization because it's just my own data" — which is how a
    self-only endpoint quietly becomes an any-profile endpoint after one refactor.
    """
    return await resolve(
        session,
        subject_id=account_id,
        account_id=account_id,
        target_profile_id=None,
        action=action,
        capacity=capacity,
    )


async def grant(
    session: AsyncSession,
    *,
    subject_id: UUID,
    target_profile_id: UUID,
    scope: GrantScope,
    grant_type: GrantType,
    source_component: str,
    source_reference_id: UUID | None = None,
) -> UUID:
    """[TR017] The only sanctioned way any component creates a grant row.

    `mangaly_authz.grant` is documented as "written only through this
    component's interface" (`models.py`) — until Home Circle needed its
    first real grant (membership => `family_info` access), nothing actually
    enforced that beyond the comment; this is that enforcement.

    `target_profile_id` is, despite the column name inherited from
    `07a-er-model.md`, the candidate's **account id** — confirmed empirically
    against the live database: `mangaly_authz.is_self()` (which every
    `target_profile_id`-keyed RLS policy in this schema calls) only matches
    `mangaly.account_id`/`mangaly.authz_context`, never a `profile.id`. A
    caller passing a real `profile.id` here would silently create a grant
    the candidate can never see as their own (`grant_visible_to_subject_or_target`
    would not recognise them), which is exactly the kind of silent-zero-rows
    failure this module's own architecture standard warns about — so this is
    stated here explicitly rather than left to be rediscovered by a second
    live failure.
    """
    grant_id = uuid4()
    await session.execute(
        text(
            """
            INSERT INTO mangaly_authz.grant
                (id, subject_id, target_profile_id, scope, grant_type,
                 status, source_component, source_reference_id)
            VALUES
                (:id, :subject_id, :target_profile_id, :scope, :grant_type,
                 'active', :source_component, :source_reference_id)
            """
        ),
        {
            "id": grant_id,
            "subject_id": subject_id,
            "target_profile_id": target_profile_id,
            "scope": scope.value,
            "grant_type": grant_type.value,
            "source_component": source_component,
            "source_reference_id": source_reference_id,
        },
    )
    # [TR069/SP069] Same transaction as the write it records.
    await bus.publish(
        session,
        schema=_SCHEMA,
        aggregate_id=grant_id,
        event_type="grant.created",
        payload={
            "grant_id": str(grant_id),
            "subject_id": str(subject_id),
            "target_profile_id": str(target_profile_id),
            "scope": scope.value,
            "grant_type": grant_type.value,
            "source_component": source_component,
        },
    )
    return grant_id


async def revoke_by_source_reference(
    session: AsyncSession,
    *,
    source_reference_id: UUID,
    grant_type: GrantType,
    source_component: str,
) -> bool:
    """Find-and-revoke the ONE grant a specific source row created, for a
    caller that never stored the grant id it wants to undo (e.g. Home Circle
    revoking the `family_info` grant a specific membership row created, at
    removal time, without adding a `grant_id` column to `membership` just to
    remember it).

    [Found live, 2026-09-13] Deliberately keyed on `source_reference_id`
    (the membership id `accept_invitation()` already passes as `grant()`'s
    `source_reference_id`) rather than the broader `(subject_id,
    target_profile_id, grant_type)` triple this function used before: the
    same two accounts can end up with more than one grant between them
    (e.g. two separate accept/remove/re-invite cycles), and matching on the
    triple alone hit a real `MultipleResultsFound` the first time two such
    grants coexisted — caught by re-running the exact same live scenario
    twice in a row, not by inspection. Matching on the specific row that
    created the grant has no such ambiguity: `source_reference_id` identifies
    exactly one membership, which created exactly one grant.
    Returns whether an active grant was actually found."""
    grant_id = (
        await session.execute(
            text(
                """
                SELECT id FROM mangaly_authz.grant
                WHERE source_reference_id = :source_reference_id
                  AND grant_type = :grant_type
                  AND status = 'active'
                """
            ),
            {"source_reference_id": source_reference_id, "grant_type": grant_type.value},
        )
    ).scalar_one_or_none()
    if grant_id is None:
        return False
    await revoke(session, grant_id=grant_id, source_component=source_component)
    return True


async def revoke(session: AsyncSession, *, grant_id: UUID, source_component: str) -> None:
    """[TR010] Immediate revocation: a plain status flip, no cache to bust.

    `resolve()` re-queries `mangaly_authz.grant` on every request (never
    caches a decision — see this module's own header comment), so the very
    next authorization check after this commits sees the revocation. There
    is nothing else to invalidate.
    """
    await session.execute(
        update(Grant)
        .where(Grant.id == grant_id, Grant.status == "active")
        .values(status="revoked", revoked_at=datetime.now(UTC))
    )
    await bus.publish(
        session,
        schema=_SCHEMA,
        aggregate_id=grant_id,
        event_type="grant.revoked",
        payload={"grant_id": str(grant_id), "source_component": source_component},
    )


async def resolve_effective_account(
    session: AsyncSession,
    *,
    acting_account_id: UUID,
    on_behalf_of_profile_id: UUID | None,
) -> UUID:
    """[BR04/BR15, first written for FR042, reused by FR021/FR026/FR030's
    family-capacity browsing] The account whose data/preferences an action
    should actually be evaluated against: the caller themselves when
    `on_behalf_of_profile_id` is absent, or — when present — the candidate
    that profile.id belongs to, but ONLY once the caller is confirmed to
    hold `family_info` on that candidate (an authorized Home Circle member,
    not merely someone who discovered the profile.id some other way).

    Resolving `on_behalf_of_profile_id` (a real `profile.id`) to its owning
    account hits the sealed schema's recurring pre-authorization RLS bind
    (`profile.lookup_account_by_profile_id()`, migration 012) — the same
    class as BLK-09-01/02/03 and migration 009, in reverse. Centralized
    here, rather than re-implemented at each call site, specifically
    because it is security-sensitive: `connection.interface.send_request()`
    duplicated this exact check inline before this helper existed, which is
    exactly the kind of logic that should have one copy, not three.

    Raises `AuthorizationDenied` (never returns a "denied" sentinel a caller
    could forget to check) when the candidate profile does not exist or the
    caller lacks the scope.
    """
    if on_behalf_of_profile_id is None:
        return acting_account_id

    from app.components.profile import interface as profile_module

    candidate_account_id = await profile_module.lookup_account_by_profile_id(
        session, profile_id=on_behalf_of_profile_id
    )
    if candidate_account_id is None:
        raise AuthorizationDenied(f"no profile exists for id {on_behalf_of_profile_id}")

    ctx = await resolve(
        session,
        subject_id=acting_account_id,
        account_id=acting_account_id,
        target_profile_id=candidate_account_id,
        action=Action.READ,
        capacity=Capacity.FAMILY,
    )
    ctx.require_scope(GrantScope.FAMILY_INFO)
    return candidate_account_id
