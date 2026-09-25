"""Home Circle — public interface.

`/MODULE-ARCHITECTURE-STANDARD.md` §3: this is the only way other components
reach Home Circle state.

Implements:
  * FR007 / TR007 — invite a person to a candidate's Home Circle.
  * FR008 / TR008 — accept an invitation (creates the membership).
  * FR009 — decline an invitation (folded into `respond_to_invitation`;
    identical exact-match/liveness contract as accept, so one function
    rather than two near-duplicates).
  * FR010 / TR010 — remove a member, or leave voluntarily.
  * FR014 / TR014 — suggest a discovered profile to the candidate.
  * FR016 / TR016 — private family notes about a match, readable only by
    their author until the author asks and the candidate agrees.

Security findings this module implements as code:
  * [Third RLS failure mode, same class as BLK-09-01/BLK-09-02] A pending
    invitation is only reachable by the invitee via
    `migrations/006-home-circle-invitation-response-functions.sql`'s two
    SECURITY DEFINER functions — a plain SELECT/UPDATE under
    `hc_invitation_participants` matches none of its three predicates before
    `invitee_account_id` is linked, which only happens on response.
  * [Confirmed live, 2026-09-13] `candidate_profile_id` on every Home Circle
    table is the candidate's ACCOUNT id, not `profile.id` — see `models.py`'s
    module docstring for how this was verified. Every write site below names
    it explicitly so it is never silently "corrected" back to a real
    profile id by a future edit.
  * TR014/SP014 — `suggest()` has no code path that reads a suggestion and
    writes a `mangaly_connection.connection_request` row. This file cannot
    even import that schema's component (`/MODULE-ARCHITECTURE-STANDARD.md`
    §3's own cross-component rule already forbids it).

Deliberately out of this pass's scope (recorded, not silently dropped):
  * "Parent invites the not-yet-registered Candidate" (M01-C §6 path B) —
    `RelationshipType` has no CANDIDATE member (a membership row represents
    someone helping, not the candidate themself), and the bootstrapping
    question of a parent originating a brand-new candidate's own account is
    a materially different flow from the other three invite paths. Skipped
    per the standing "skip and mark, do not block" instruction.
  * `report()` (M01-C §8's false-relationship-claim reporting) — not one of
    this pass's five assigned FRs; `report` table exists live but has no
    interface function yet.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.components.authorization import interface as authz
from app.components.authorization.context import Action, GrantScope, GrantType
from app.components.home_circle.models import (
    Invitation,
    InvitationStatus,
    Membership,
    MembershipStatus,
    RelationshipType,
)
from app.components.identity_bridge import interface as identity
from app.config.settings import get_settings
from app.events import bus
from app.rate_limiting import limiter

__all__ = [
    "AlreadyMember",
    "InvitationNotFound",
    "InviteSelf",
    "CandidateNotOnForKhatri",
    "PersonSummary",
    "search_people",
    "MemberSummary",
    "NotFound",
    "PendingInvitationSummary",
    "FamilyNote",
    "InvalidNoteSubject",
    "NoteForwardRequest",
    "SharedNote",
    "NOTE_MAX_LENGTH",
    "RateLimited",
    "accept_invitation",
    "decline_invitation",
    "add_note",
    "decide_note_request",
    "delete_note",
    "edit_note",
    "get_membership_candidate",
    "invite",
    "leave",
    "SuggestionSummary",
    "list_home_circle",
    "list_circle_members",
    "CircleMember",
    "list_member_contexts",
    "MemberContext",
    "list_my_notes",
    "list_note_requests",
    "list_shared_notes",
    "list_pending_invitations",
    "list_suggestions",
    "remove_member",
    "suggest",
    "request_note_forward",
]

_SOURCE = "home_circle"


class RateLimited(Exception):
    """[SP007] Carries the retry-after so the caller can render it, matching
    Identity Bridge's own `RateLimited` shape."""

    def __init__(self, retry_after_seconds: int) -> None:
        super().__init__(f"retry after {retry_after_seconds}s")
        self.retry_after_seconds = retry_after_seconds


class InviteSelf(Exception):
    """[FR007 failure outcome] An account cannot invite its own identifier."""


class AlreadyMember(Exception):
    """[FR007 failure outcome] The identifier already has an active
    membership, or an unexpired pending invitation, for this candidate."""


class InvitationNotFound(Exception):
    """[FR008/FR009 failure outcome] No pending invitation matched — expired,
    already responded to, wrong identifier, or never existed. Deliberately
    one exception for all four: SP092-class anti-enumeration reasoning
    applies here too (an invitee should not learn *which* case it was)."""


class NotFound(Exception):
    """Generic "no such row, or not visible to this caller" outcome."""


class CandidateNotOnForKhatri(Exception):
    """[FR007 path B] A `to_candidate` invitation names a candidate who has no
    ForKhatri account yet: there is no account to own the circle."""


@dataclass(frozen=True, slots=True)
class PendingInvitationSummary:
    id: UUID
    candidate_account_id: UUID
    inviter_account_id: UUID
    relationship_type: RelationshipType
    created_at: datetime
    expires_at: datetime | None
    # [Migration 030] `to_member` (join the candidate's circle) or
    # `to_candidate` (the inviter asks the invitee — a candidate — to let them
    # join the invitee's circle as `relationship_type`).
    direction: str = "to_member"
    inviter_name: str | None = None
    candidate_name: str | None = None
    relation: str | None = None


@dataclass(frozen=True, slots=True)
class MemberSummary:
    membership_id: UUID
    member_account_id: UUID
    relationship_type: RelationshipType
    status: MembershipStatus
    joined_at: datetime


async def invite(
    session: AsyncSession,
    *,
    inviter_account_id: UUID,
    candidate_account_id: UUID,
    relationship_type: RelationshipType,
    invitee_identifier: str | None = None,
    invitee_account_id: UUID | None = None,
    direction: str = "to_member",
    relation: str | None = None,
) -> UUID:
    """[FR007/TR007, DEC-V1-022] Invite someone into a Home Circle. Three paths,
    one function (rework contract §3/§6):

      * candidate → family (`to_member`, inviter == candidate): the invitee
        joins the inviter's circle as `relationship_type`.
      * member → relative (`to_member`, inviter != candidate): the caller,
        already in `candidate_account_id`'s circle (the route checked
        `family_info`), invites another person into that same circle.
      * family → candidate (`to_candidate`): the inviter — with or without a
        profile or any circle of their own — asks a CANDIDATE to let them join
        the candidate's circle as `relationship_type`. `candidate_account_id`
        is then the invitee's own account, which must already exist on
        ForKhatri (`CandidateNotOnForKhatri` otherwise).

    The invitee is addressed by account id (from `search_people`) or by phone/
    email; whichever is known is stored, and both response functions match on
    either (migration 030). Any signed-in account may invite.
    """
    settings = get_settings()
    try:
        await limiter.enforce_durable(
            scope=limiter.RateLimitScope.HOME_CIRCLE_INVITE,
            subject=str(inviter_account_id),
            limit_max=settings.rate_limit_home_circle_invite_max,
            window_seconds=settings.rate_limit_default_window_seconds,
        )
    except limiter.RateLimitExceeded as exc:
        raise RateLimited(exc.result.retry_after_seconds) from exc

    if direction not in ("to_member", "to_candidate"):
        raise ValueError("direction must be to_member or to_candidate")
    identifier = (invitee_identifier or "").strip() or None
    if identifier is None and invitee_account_id is None:
        raise InviteSelf  # nothing to address; treated as an invalid invite

    inviter_phone, inviter_email = await identity.get_own_identifiers(
        session, account_id=inviter_account_id
    )
    # `identifier` is None when the invitee was picked by account id, and a
    # member with no email has `inviter_email` None — so compare only real
    # values, or `None in (phone, None)` rejects every pick-by-name invite.
    own = {i for i in (inviter_phone, inviter_email) if i}
    if (identifier is not None and identifier in own) or invitee_account_id == inviter_account_id:
        raise InviteSelf

    # Resolve the other half of the address when we can: an account id from
    # people search gets its identifier; a typed identifier gets its account.
    if invitee_account_id is not None and identifier is None:
        identifier = (
            await session.execute(
                text("SELECT mangaly_identity.primary_identifier_of(:id)"),
                {"id": invitee_account_id},
            )
        ).scalar_one_or_none()
    if identifier is not None and identifier in own:
        raise InviteSelf
    if invitee_account_id is None and identifier is not None:
        invitee_account_id = (
            await session.execute(
                text("SELECT mangaly_identity.account_id_for_identifier(:identifier)"),
                {"identifier": identifier},
            )
        ).scalar_one_or_none()

    if direction == "to_candidate":
        if invitee_account_id is None:
            raise CandidateNotOnForKhatri
        candidate_account_id = invitee_account_id
        member_account_id: UUID | None = inviter_account_id
    else:
        member_account_id = invitee_account_id
    if candidate_account_id == member_account_id:
        raise InviteSelf

    if member_account_id is not None:
        active = (
            await session.execute(
                text(
                    "SELECT 1 FROM mangaly_home_circle.membership "
                    "WHERE candidate_profile_id = :candidate AND member_account_id = :member "
                    "AND status = 'active' LIMIT 1"
                ),
                {"candidate": candidate_account_id, "member": member_account_id},
            )
        ).first()
        if active is not None:
            raise AlreadyMember

    existing = (
        await session.execute(
            text(
                "SELECT 1 FROM mangaly_home_circle.invitation "
                "WHERE candidate_profile_id = :candidate AND status = 'pending' "
                "AND direction = :direction "
                "AND ((CAST(:identifier AS text) IS NOT NULL AND invitee_identifier = :identifier) "
                "     OR (CAST(:invitee AS uuid) IS NOT NULL AND invitee_account_id = :invitee)) "
                "LIMIT 1"
            ),
            {
                "candidate": candidate_account_id,
                "direction": direction,
                "identifier": identifier,
                "invitee": invitee_account_id,
            },
        )
    ).first()
    if existing is not None:
        raise AlreadyMember

    invitation_id = uuid4()
    await session.execute(
        text(
            """
            INSERT INTO mangaly_home_circle.invitation
                (id, candidate_profile_id, inviter_account_id, invitee_identifier,
                 invitee_account_id, relationship_type, status, direction, relation)
            VALUES (:id, :candidate, :inviter, :identifier, :invitee, :relationship,
                    'pending', :direction, :relation)
            """
        ),
        {
            "id": invitation_id,
            "candidate": candidate_account_id,
            "inviter": inviter_account_id,
            "identifier": identifier,
            "invitee": invitee_account_id,
            "relationship": relationship_type.value,
            "direction": direction,
            "relation": relation,
        },
    )
    await bus.publish(
        session,
        schema="mangaly_home_circle",
        aggregate_id=invitation_id,
        event_type="HomeCircleInvitationSent",
        payload={
            "invitation_id": str(invitation_id),
            "candidate_account_id": str(candidate_account_id),
            "inviter_account_id": str(inviter_account_id),
            "relationship_type": relationship_type.value,
            "direction": direction,
        },
    )
    if invitee_account_id is not None:
        from app.components.notification_bridge import interface as notifications

        await notifications.notify(
            session,
            recipients=[invitee_account_id],
            subject_account_id=invitee_account_id,
            kind="invitation_received",
            payload={
                "invitation_id": invitation_id,
                "relationship": relationship_type.value,
                "direction": direction,
            },
            link="/circle",
        )
    return invitation_id


async def list_pending_invitations(
    session: AsyncSession, *, account_id: UUID
) -> list[PendingInvitationSummary]:
    """[FR008] The caller's own pending invitations — addressed to their account
    id or to their phone/email. Goes through the SECURITY DEFINER function from
    migration 030; see this module's docstring for why a plain SELECT cannot
    see these rows at all."""
    phone, email = await identity.get_own_identifiers(session, account_id=account_id)
    identifiers = [i for i in (phone, email) if i is not None]

    rows = await session.execute(
        text(
            "SELECT * FROM mangaly_home_circle.list_pending_invitations_for("
            ":account_id, CAST(:identifiers AS text[]))"
        ),
        {"account_id": account_id, "identifiers": identifiers},
    )
    return [
        PendingInvitationSummary(
            id=row.id,
            candidate_account_id=row.candidate_profile_id,
            inviter_account_id=row.inviter_account_id,
            relationship_type=RelationshipType(row.relationship_type),
            created_at=row.created_at,
            expires_at=row.expires_at,
            direction=row.direction,
            inviter_name=row.inviter_name,
            candidate_name=row.candidate_name,
            relation=row.relation,
        )
        for row in rows
    ]


@dataclass(frozen=True, slots=True)
class _Response:
    candidate_account_id: UUID
    relationship_type: RelationshipType
    inviter_account_id: UUID
    direction: str
    relation: str | None = None


async def _respond(
    session: AsyncSession, *, invitation_id: UUID, account_id: UUID, response: InvitationStatus
) -> _Response:
    phone, email = await identity.get_own_identifiers(session, account_id=account_id)
    identifiers = [i for i in (phone, email) if i is not None]
    row = (
        await session.execute(
            text(
                "SELECT candidate_profile_id, relationship_type, inviter_account_id, direction, relation "
                "FROM mangaly_home_circle.respond_to_invitation"
                "(:id, :account, CAST(:identifiers AS text[]), :response)"
            ),
            {
                "id": invitation_id,
                "account": account_id,
                "identifiers": identifiers,
                "response": response.value,
            },
        )
    ).first()
    if row is None:
        raise InvitationNotFound
    return _Response(
        candidate_account_id=row.candidate_profile_id,
        relationship_type=RelationshipType(row.relationship_type),
        inviter_account_id=row.inviter_account_id,
        direction=row.direction,
        relation=row.relation,
    )


async def accept_invitation(
    session: AsyncSession, *, invitation_id: UUID, account_id: UUID
) -> UUID:
    """[FR008/TR008] Accept: links the invitation, creates the membership,
    grants `family_info` scope, publishes `HomeCircleMemberJoined` — all in
    the caller's one transaction (TR069's outbox rule).

    [Migration 030] For a `to_candidate` invitation the accepter IS the
    candidate and the inviter becomes the member; for `to_member` the
    accepter joins the named candidate's circle."""
    answer = await _respond(
        session,
        invitation_id=invitation_id,
        account_id=account_id,
        response=InvitationStatus.ACCEPTED,
    )
    if answer.direction == "to_candidate":
        candidate_account_id = account_id
        member_account_id = answer.inviter_account_id
    else:
        candidate_account_id = answer.candidate_account_id
        member_account_id = account_id
    relationship_type = answer.relationship_type

    membership_id = uuid4()
    await session.execute(
        text(
            """
            INSERT INTO mangaly_home_circle.membership
                (id, candidate_profile_id, member_account_id, invitation_id,
                 relationship_type, status, relation)
            VALUES (:id, :candidate, :member, :invitation, :relationship, 'active', :relation)
            """
        ),
        {
            "id": membership_id,
            "candidate": candidate_account_id,
            "member": member_account_id,
            "invitation": invitation_id,
            "relationship": relationship_type.value,
            "relation": answer.relation,
        },
    )

    await authz.grant(
        session,
        subject_id=member_account_id,
        target_profile_id=candidate_account_id,
        scope=GrantScope.FAMILY_INFO,
        grant_type=GrantType.HOME_CIRCLE_MEMBERSHIP,
        source_component=_SOURCE,
        source_reference_id=membership_id,
    )

    await bus.publish(
        session,
        schema="mangaly_home_circle",
        aggregate_id=membership_id,
        event_type="HomeCircleMemberJoined",
        payload={
            "membership_id": str(membership_id),
            "candidate_account_id": str(candidate_account_id),
            "member_account_id": str(member_account_id),
            "relationship_type": relationship_type.value,
        },
    )
    # [Migration 037] A new member is added to the family conversations their
    # candidate already has open.
    await session.execute(
        text("SELECT mangaly_communication.sync_family_participants_for(:candidate)"),
        {"candidate": candidate_account_id},
    )
    return membership_id


async def add_founding_member(
    session: AsyncSession, *, candidate_account_id: UUID, member_account_id: UUID, relation: str
) -> UUID:
    """[DEC-V1-019] The person who creates a profile for their son or daughter
    is its circle's first member — as their exact relation, with the same
    `family_info` grant an accepted invitation gives. Must run with the
    CANDIDATE's account bound (the membership and grant policies admit the
    candidate), exactly like accepting a `to_candidate` invitation."""
    from app.components.home_circle.models import RELATION_ROLE

    role = RELATION_ROLE[relation]
    membership_id = uuid4()
    await session.execute(
        text(
            """
            INSERT INTO mangaly_home_circle.membership
                (id, candidate_profile_id, member_account_id, invitation_id,
                 relationship_type, status, relation)
            VALUES (:id, :candidate, :member, NULL, :relationship, 'active', :relation)
            """
        ),
        {
            "id": membership_id,
            "candidate": candidate_account_id,
            "member": member_account_id,
            "relationship": role.value,
            "relation": relation,
        },
    )
    await authz.grant(
        session,
        subject_id=member_account_id,
        target_profile_id=candidate_account_id,
        scope=GrantScope.FAMILY_INFO,
        grant_type=GrantType.HOME_CIRCLE_MEMBERSHIP,
        source_component=_SOURCE,
        source_reference_id=membership_id,
    )
    await bus.publish(
        session,
        schema="mangaly_home_circle",
        aggregate_id=membership_id,
        event_type="HomeCircleMemberJoined",
        payload={
            "membership_id": str(membership_id),
            "candidate_account_id": str(candidate_account_id),
            "member_account_id": str(member_account_id),
            "relationship_type": role.value,
        },
    )
    return membership_id


async def decline_invitation(
    session: AsyncSession, *, invitation_id: UUID, account_id: UUID
) -> None:
    """[FR009] Decline: an explicit, independently-queryable status — never
    inferred from silent expiry (TR009)."""
    await _respond(
        session,
        invitation_id=invitation_id,
        account_id=account_id,
        response=InvitationStatus.DECLINED,
    )


async def set_relation(
    session: AsyncSession, *, membership_id: UUID, caller_account_id: UUID, relation: str
) -> bool:
    """[Migration 040] State the exact relation on a membership — and so its role.

    Only the two people the row is about may say how they are related: the
    candidate, or the member themselves. The membership RLS policy also admits
    other family members (they may READ the circle), so this check is made here,
    not left to RLS. Returns False when the caller may not, or the row is gone."""
    from app.components.home_circle.models import RELATION_ROLE

    role = RELATION_ROLE[relation]
    result = await session.execute(
        text(
            "UPDATE mangaly_home_circle.membership "
            "SET relation = :relation, relationship_type = :role, updated_at = now() "
            "WHERE id = :id AND status = 'active' "
            "AND (candidate_profile_id = :caller OR member_account_id = :caller)"
        ),
        {"relation": relation, "role": role.value, "id": membership_id, "caller": caller_account_id},
    )
    return result.rowcount == 1


async def get_membership_candidate(session: AsyncSession, *, membership_id: UUID) -> UUID | None:
    """Resolve which candidate's circle a membership belongs to — needed by
    `suggest()`/`write_note()` callers, since one account can be an active
    member of more than one candidate's circle at once. A plain SELECT: RLS
    already restricts this to memberships the caller is actually part of
    (`is_self(member_account_id)`), so there is nothing here for a caller to
    probe about a circle they are not in."""
    return (
        await session.execute(
            select(Membership.candidate_profile_id).where(Membership.id == membership_id)
        )
    ).scalar_one_or_none()


async def list_home_circle(
    session: AsyncSession, *, candidate_account_id: UUID
) -> list[MemberSummary]:
    """[FR012-adjacent read] The candidate's own active members, newest last
    (M01-C: membership can grow from different directions, so no single
    "leader" ordering is implied by row order)."""
    rows = (
        await session.execute(
            select(Membership)
            .where(
                Membership.candidate_profile_id == candidate_account_id,
                Membership.status == MembershipStatus.ACTIVE,
            )
            .order_by(Membership.joined_at)
        )
    ).scalars()
    return [
        MemberSummary(
            membership_id=m.id,
            member_account_id=m.member_account_id,
            relationship_type=m.relationship_type,
            status=m.status,
            joined_at=m.joined_at,
        )
        for m in rows
    ]


async def _end_membership(
    session: AsyncSession, *, membership_id: UUID, new_status: MembershipStatus
) -> None:
    row = (
        await session.execute(
            select(Membership).where(
                Membership.id == membership_id, Membership.status == MembershipStatus.ACTIVE
            )
        )
    ).scalar_one_or_none()
    if row is None:
        raise NotFound

    await session.execute(
        text(
            "UPDATE mangaly_home_circle.membership "
            "SET status = :status, removed_at = :removed_at, updated_at = :removed_at "
            "WHERE id = :id"
        ),
        {"status": new_status.value, "removed_at": datetime.now(UTC), "id": membership_id},
    )

    # [TR010] Immediate revocation — `authorization.interface.resolve()`
    # re-queries on every request, so this is the only step that matters.
    # Keyed on THIS membership's own grant (via `source_reference_id`), not
    # the broader (subject, target, type) triple — the same two accounts can
    # have more than one grant between them across separate membership
    # cycles (found live; see `revoke_by_source_reference()`'s docstring).
    await authz.revoke_by_source_reference(
        session,
        source_reference_id=membership_id,
        grant_type=GrantType.HOME_CIRCLE_MEMBERSHIP,
        source_component=_SOURCE,
    )
    # [FR048] A former member's phone must not stay shared with, or requested
    # for, any connection (migration 021).
    await session.execute(
        text("SELECT mangaly_connection.end_family_contact_for_member(:candidate_id, :member_id)"),
        {"candidate_id": row.candidate_profile_id, "member_id": row.member_account_id},
    )

    removed = new_status is MembershipStatus.REMOVED
    event_type = "HomeCircleMemberRemoved" if removed else "HomeCircleMemberLeft"
    await bus.publish(
        session,
        schema="mangaly_home_circle",
        aggregate_id=membership_id,
        event_type=event_type,
        payload={
            "membership_id": str(membership_id),
            "candidate_account_id": str(row.candidate_profile_id),
            "member_account_id": str(row.member_account_id),
        },
    )


async def remove_member(session: AsyncSession, *, membership_id: UUID) -> None:
    """[FR010/TR010] The candidate removes a member. `AuthenticatedAccount`'s
    own RLS binding is what actually restricts this to the real candidate —
    `hc_membership_participants` denies the UPDATE outright for anyone else,
    so this function does not re-check identity itself (CODING-GUIDE.md §3:
    the database is the enforcement point, not a second application check
    that could drift from it)."""
    await _end_membership(session, membership_id=membership_id, new_status=MembershipStatus.REMOVED)


async def leave(session: AsyncSession, *, membership_id: UUID) -> None:
    """[FR010/M01-C §9] A member leaves voluntarily — no other member's
    approval required; the same RLS predicate (`is_self(member_account_id)`)
    that lets a candidate remove someone else also lets a member remove
    themselves, so this is the same underlying operation with a different
    resulting status."""
    await _end_membership(session, membership_id=membership_id, new_status=MembershipStatus.LEFT)


async def suggest(
    session: AsyncSession,
    *,
    member_account_id: UUID,
    membership_id: UUID,
    candidate_account_id: UUID,
    suggested_profile_id: UUID,
    note: str | None,
) -> UUID:
    """[FR014/TR014] Suggestion only — structurally incapable of becoming a
    connection request (see this module's docstring).

    [TR017] Binds `mangaly.authz_context` via the one sanctioned chokepoint
    before the INSERT: `hc_suggestion_family`'s RLS policy is gated entirely
    on `has_scope(candidate,'family_info')`, which reads
    `mangaly.authz_context` — a variable only `authorization.interface.resolve()`
    ever sets. Skipping this call is not a hardening gap, it is a hard
    failure: the INSERT is rejected outright by RLS (found live, 2026-09-13,
    via a real 500 from `InsufficientPrivilegeError`, not by inspection).
    """
    await authz.resolve(
        session,
        subject_id=member_account_id,
        account_id=member_account_id,
        target_profile_id=candidate_account_id,
        action=Action.WRITE,
    )

    suggestion_id = uuid4()
    await session.execute(
        text(
            """
            INSERT INTO mangaly_home_circle.suggestion
                (id, candidate_profile_id, suggested_by_membership_id, suggested_profile_id, note)
            VALUES (:id, :candidate, :membership, :profile, :note)
            """
        ),
        {
            "id": suggestion_id,
            "candidate": candidate_account_id,
            "membership": membership_id,
            "profile": suggested_profile_id,
            "note": note,
        },
    )
    await bus.publish(
        session,
        schema="mangaly_home_circle",
        aggregate_id=suggestion_id,
        event_type="HomeCircleProfileSuggested",
        payload={
            "suggestion_id": str(suggestion_id),
            "candidate_account_id": str(candidate_account_id),
            "suggested_by_membership_id": str(membership_id),
            "suggested_profile_id": str(suggested_profile_id),
        },
    )
    from app.components.notification_bridge import interface as notifications

    await notifications.notify(
        session,
        recipients=[candidate_account_id],
        subject_account_id=candidate_account_id,
        kind="suggestion_received",
        payload={"suggestion_id": suggestion_id, "suggested_account_id": suggested_profile_id},
        link="/circle/suggestions",
    )
    return suggestion_id


@dataclass(frozen=True, slots=True)
class SuggestionSummary:
    id: UUID
    suggested_profile_id: UUID
    suggested_by_relationship_type: RelationshipType
    note: str | None
    created_at: datetime
    # [Migration 040] Who suggested it, and their exact relation.
    suggested_by_account_id: UUID | None = None
    suggested_by_relation: str | None = None


async def list_suggestions(
    session: AsyncSession, *, caller_account_id: UUID, candidate_account_id: UUID
) -> list[SuggestionSummary]:
    """[FR014] Every suggestion made to one candidate — visible to the
    candidate themselves (self-read) and to any other family member sharing
    that same Home Circle (so a suggestion is a shared circle activity, not
    a private channel to only the suggester and the candidate). Never
    returns the suggested profile's name/photo: the caller resolves
    `suggested_profile_id` through `discovery.interface.get_snippet()` —
    the same pre-connection-safe demographic snippet every other
    not-yet-connected candidate is shown as, since a family-forwarded
    suggestion is not itself a connection or a consent event (FR021's
    identity-protection boundary does not move for this feature).

    [TR017] Same chokepoint pattern as `list_notes()` — a no-op self-bypass
    when the caller IS the candidate, a real `family_info` scope check
    otherwise.
    """
    await authz.resolve(
        session,
        subject_id=caller_account_id,
        account_id=caller_account_id,
        target_profile_id=candidate_account_id,
        action=Action.READ,
    )
    rows = (
        await session.execute(
            text(
                """
                SELECT s.id, s.suggested_profile_id, s.note, s.created_at,
                       m.relationship_type, m.relation, m.member_account_id
                FROM mangaly_home_circle.suggestion s
                JOIN mangaly_home_circle.membership m ON m.id = s.suggested_by_membership_id
                WHERE s.candidate_profile_id = :candidate
                ORDER BY s.created_at DESC
                """
            ),
            {"candidate": candidate_account_id},
        )
    ).mappings()
    return [
        SuggestionSummary(
            id=row["id"],
            suggested_profile_id=row["suggested_profile_id"],
            suggested_by_relationship_type=RelationshipType(row["relationship_type"]),
            suggested_by_account_id=row["member_account_id"],
            suggested_by_relation=row["relation"],
            note=row["note"],
            created_at=row["created_at"],
        )
        for row in rows
    ]


NOTE_MAX_LENGTH = 1000

_NOTE_COLUMNS = (
    "id, subject_account_id, content, forwarded_at, forward_requested_at, "
    "forward_declined_at, created_at, updated_at"
)


class InvalidNoteSubject(Exception):
    """[FR016] A note is about a match — never about the candidate or the author."""


@dataclass(frozen=True, slots=True)
class FamilyNote:
    """[FR016] One of the author's own private notes about one match.

    `status` is `private` (only the author has ever seen it), `requested`
    (the author asked the candidate to read it), `shared` (the candidate
    agreed and can read it) or `declined` (the candidate said not now; no
    reason is ever recorded or shown)."""

    id: UUID
    subject_account_id: UUID
    content: str
    status: str
    created_at: datetime
    updated_at: datetime


def _family_note(row: Any) -> FamilyNote:
    if row.forwarded_at is not None:
        note_status = "shared"
    elif row.forward_declined_at is not None:
        note_status = "declined"
    elif row.forward_requested_at is not None:
        note_status = "requested"
    else:
        note_status = "private"
    return FamilyNote(
        id=row.id,
        subject_account_id=row.subject_account_id,
        content=row.content,
        status=note_status,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


async def _own_active_membership_candidate(
    session: AsyncSession, *, membership_id: UUID, member_account_id: UUID
) -> UUID | None:
    """The candidate whose circle `membership_id` is, but only when the caller
    is that membership's own active member — a candidate passing an id from
    their own circle gets nothing."""
    return (
        await session.execute(
            select(Membership.candidate_profile_id).where(
                Membership.id == membership_id,
                Membership.member_account_id == member_account_id,
                Membership.status == MembershipStatus.ACTIVE,
            )
        )
    ).scalar_one_or_none()


async def add_note(
    session: AsyncSession,
    *,
    member_account_id: UUID,
    membership_id: UUID,
    subject_account_id: UUID,
    content: str,
) -> FamilyNote:
    """[FR016/TR016] A Home Circle member writes a private working note about
    one match. Only its author can read it (`hc_note_author`, migration 022);
    the candidate and every other member of the circle cannot (TS035).

    [TR017] Binds the authorization chokepoint for the candidate's circle, the
    same way `suggest()` does."""
    candidate_account_id = await _own_active_membership_candidate(
        session, membership_id=membership_id, member_account_id=member_account_id
    )
    if candidate_account_id is None:
        raise NotFound
    if subject_account_id in (candidate_account_id, member_account_id):
        raise InvalidNoteSubject
    await authz.resolve(
        session,
        subject_id=member_account_id,
        account_id=member_account_id,
        target_profile_id=candidate_account_id,
        action=Action.WRITE,
    )
    row = (
        await session.execute(
            text(
                "INSERT INTO mangaly_home_circle.home_circle_note "
                "(candidate_profile_id, author_membership_id, subject_account_id, content) "
                "VALUES (:candidate, :membership, :subject, :content) "
                f"RETURNING {_NOTE_COLUMNS}"
            ),
            {
                "candidate": candidate_account_id,
                "membership": membership_id,
                "subject": subject_account_id,
                "content": content,
            },
        )
    ).one()
    return _family_note(row)


async def list_my_notes(
    session: AsyncSession,
    *,
    member_account_id: UUID,
    membership_id: UUID,
    subject_account_id: UUID,
) -> list[FamilyNote]:
    """[FR016] The caller's own notes about one match, newest first."""
    if (
        await _own_active_membership_candidate(
            session, membership_id=membership_id, member_account_id=member_account_id
        )
        is None
    ):
        raise NotFound
    rows = await session.execute(
        text(
            f"SELECT {_NOTE_COLUMNS} FROM mangaly_home_circle.home_circle_note "
            "WHERE author_membership_id = :membership AND subject_account_id = :subject "
            "ORDER BY created_at DESC"
        ),
        {"membership": membership_id, "subject": subject_account_id},
    )
    return [_family_note(r) for r in rows]


async def edit_note(session: AsyncSession, *, note_id: UUID, content: str) -> FamilyNote:
    """[FR016] The author rewrites a note that has not been shared. Editing
    takes it back to private: the candidate is only ever asked about the exact
    words they would read. A shared note is fixed — the author may delete it,
    but never change what the candidate agreed to read."""
    row = (
        await session.execute(
            text(
                "UPDATE mangaly_home_circle.home_circle_note "
                "SET content = :content, updated_at = now(), "
                "forward_requested_at = NULL, forward_declined_at = NULL "
                "WHERE id = :id AND forwarded_at IS NULL "
                f"RETURNING {_NOTE_COLUMNS}"
            ),
            {"id": note_id, "content": content},
        )
    ).one_or_none()
    if row is None:
        raise NotFound
    return _family_note(row)


async def delete_note(session: AsyncSession, *, note_id: UUID) -> None:
    """[FR016] The author deletes one of their notes (RLS: author only)."""
    deleted = (
        await session.execute(
            text("DELETE FROM mangaly_home_circle.home_circle_note WHERE id = :id RETURNING id"),
            {"id": note_id},
        )
    ).one_or_none()
    if deleted is None:
        raise NotFound


async def request_note_forward(session: AsyncSession, *, note_id: UUID) -> FamilyNote:
    """[FR016/UX13] The author asks the candidate to read this one note. Asking
    again after "not now" needs a changed note, so a "no" is never answered
    with the same request."""
    row = (
        await session.execute(
            text(
                "UPDATE mangaly_home_circle.home_circle_note "
                "SET forward_requested_at = now() "
                "WHERE id = :id AND forwarded_at IS NULL AND forward_requested_at IS NULL "
                f"RETURNING candidate_profile_id, {_NOTE_COLUMNS}"
            ),
            {"id": note_id},
        )
    ).one_or_none()
    if row is None:
        raise NotFound
    await bus.publish(
        session,
        schema="mangaly_home_circle",
        aggregate_id=note_id,
        event_type="FamilyNoteReadRequested",
        payload={"note_id": str(note_id), "candidate_account_id": str(row.candidate_profile_id)},
    )
    from app.components.notification_bridge import interface as notifications

    await notifications.notify(
        session,
        recipients=[row.candidate_profile_id],
        subject_account_id=row.candidate_profile_id,
        kind="note_forwarded",
        payload={"note_id": note_id, "subject_account_id": row.subject_account_id},
        link="/circle/notes",
    )
    return _family_note(row)


@dataclass(frozen=True, slots=True)
class NoteForwardRequest:
    """[FR016] What the candidate sees before choosing: who asks and which
    match the note is about — never the note's words."""

    note_id: UUID
    author_name: str | None
    relationship_type: str
    subject_account_id: UUID
    requested_at: datetime


async def list_note_requests(
    session: AsyncSession, *, account_id: UUID
) -> list[NoteForwardRequest]:
    rows = await session.execute(
        text("SELECT * FROM mangaly_home_circle.list_note_forward_requests(:account_id)"),
        {"account_id": account_id},
    )
    return [
        NoteForwardRequest(
            note_id=r.note_id,
            author_name=r.author_name,
            relationship_type=r.relationship_type,
            subject_account_id=r.subject_account_id,
            requested_at=r.requested_at,
        )
        for r in rows
    ]


async def decide_note_request(
    session: AsyncSession, *, account_id: UUID, note_id: UUID, approve: bool
) -> str | None:
    """[FR016/TS036] The candidate reads one note, or says not now. Agreeing
    shares only that note; returns its words so they appear in place."""
    decided = (
        await session.execute(
            text("SELECT mangaly_home_circle.decide_note_forward(:note_id, :account_id, :approve)"),
            {"note_id": note_id, "account_id": account_id, "approve": approve},
        )
    ).scalar_one()
    if not decided:
        raise NotFound
    await bus.publish(
        session,
        schema="mangaly_home_circle",
        aggregate_id=note_id,
        event_type="FamilyNoteRead" if approve else "FamilyNoteDeclined",
        payload={"note_id": str(note_id)},
    )
    if not approve:
        return None
    return (
        await session.execute(
            text("SELECT content FROM mangaly_home_circle.home_circle_note WHERE id = :id"),
            {"id": note_id},
        )
    ).scalar_one()


@dataclass(frozen=True, slots=True)
class SharedNote:
    note_id: UUID
    content: str
    author_name: str | None
    relationship_type: str
    subject_account_id: UUID
    forwarded_at: datetime


async def list_shared_notes(session: AsyncSession, *, account_id: UUID) -> list[SharedNote]:
    """[FR016] Notes the candidate chose to read, newest first."""
    rows = await session.execute(
        text("SELECT * FROM mangaly_home_circle.list_shared_notes(:account_id)"),
        {"account_id": account_id},
    )
    return [
        SharedNote(
            note_id=r.note_id,
            content=r.content,
            author_name=r.author_name,
            relationship_type=r.relationship_type,
            subject_account_id=r.subject_account_id,
            forwarded_at=r.forwarded_at,
        )
        for r in rows
    ]


@dataclass(frozen=True, slots=True)
class MemberContext:
    membership_id: UUID
    candidate_account_id: UUID
    candidate_name: str
    relationship_type: RelationshipType
    joined_at: datetime
    # [Migration 030] What the identity payload carries per circle.
    candidate_profile_id: UUID | None = None
    member_count: int = 0
    looking_for: str | None = None
    primary_photo_ref: str | None = None
    relation: str | None = None


async def list_member_contexts(session: AsyncSession, *, account_id: UUID) -> list[MemberContext]:
    """[FR097] The candidates whose Home Circle the caller actively belongs to:
    the searches they may act in besides their own. Names come through
    `list_member_contexts()` (migrations 017/030), because a family grant does
    not unlock the candidate's profile row; a candidate who has not created a
    profile yet is named from their ForKhatri display name."""
    rows = await session.execute(
        text("SELECT * FROM mangaly_home_circle.list_member_contexts(:account_id)"),
        {"account_id": account_id},
    )
    return [
        MemberContext(
            membership_id=r["membership_id"],
            candidate_account_id=r["candidate_account_id"],
            candidate_name=r["candidate_name"] or "",
            relationship_type=RelationshipType(r["relationship_type"]),
            joined_at=r["joined_at"],
            candidate_profile_id=r["candidate_profile_id"],
            member_count=int(r["member_count"] or 0),
            looking_for=r["looking_for"],
            primary_photo_ref=r["primary_photo_ref"],
            relation=r["relation"],
        )
        for r in rows.mappings()
    ]


@dataclass(frozen=True, slots=True)
class PersonSummary:
    """[Rework contract §6] One ForKhatri member found by name or phone."""

    account_id: UUID
    display_name: str | None
    phone_masked: str | None
    has_profile: bool


async def search_people(session: AsyncSession, *, q: str) -> list[PersonSummary]:
    """[Rework contract §6] Find people to invite, by name or phone. The
    identity service exposes only an id-based member lookup, so this searches
    Mangaly's own member-link rows (id = platform member id) through
    `mangaly_identity.search_people()` (migration 030): signed-in callers only,
    never the caller themselves, phone masked, at most 20 rows."""
    cleaned = (q or "").strip()
    if len(cleaned) < 2:
        return []
    rows = await session.execute(
        text("SELECT * FROM mangaly_identity.search_people(:q)"), {"q": cleaned}
    )
    return [
        PersonSummary(
            account_id=r["account_id"],
            display_name=r["display_name"],
            phone_masked=r["phone_masked"],
            has_profile=bool(r["has_profile"]),
        )
        for r in rows.mappings()
    ]


@dataclass(frozen=True, slots=True)
class CircleMember:
    membership_id: UUID
    member_account_id: UUID
    member_name: str | None
    relationship_type: RelationshipType
    joined_at: datetime
    relation: str | None = None


async def list_circle_members(
    session: AsyncSession, *, candidate_account_id: UUID
) -> list[CircleMember]:
    """The candidate's own active members with their names. Names come through
    `list_circle_members()` (migration 019), since member link rows are
    otherwise readable only by the member themselves."""
    rows = await session.execute(
        text("SELECT * FROM mangaly_home_circle.list_circle_members(:candidate)"),
        {"candidate": candidate_account_id},
    )
    return [
        CircleMember(
            membership_id=r["membership_id"],
            member_account_id=r["member_account_id"],
            member_name=r["member_name"],
            relationship_type=RelationshipType(r["relationship_type"]),
            joined_at=r["joined_at"],
            relation=r["relation"],
        )
        for r in rows.mappings()
    ]


async def list_circle_for(
    session: AsyncSession, *, caller_account_id: UUID, candidate_account_id: UUID
) -> list[CircleMember]:
    """[FR012 read, 2026-09-17] One candidate's Home Circle, read either by the
    candidate themselves or by a family member of that same circle.

    A parent's Circle screen has to show the same people the candidate's own
    screen shows — the owner's words were "that contains home circle people
    always" — so the family capacity needs the identical read, not a reduced
    one. Same chokepoint shape as `list_suggestions()`: `authz.resolve()` is a
    no-op self-bypass when the caller IS the candidate and a real `family_info`
    check otherwise, and migration 025 widened
    `mangaly_home_circle.list_circle_members()`'s own predicate to match the
    membership rows' existing RLS policy so the name projection is no longer
    narrower than the rows it reads."""
    await authz.resolve(
        session,
        subject_id=caller_account_id,
        account_id=caller_account_id,
        target_profile_id=candidate_account_id,
        action=Action.READ,
    )
    return await list_circle_members(session, candidate_account_id=candidate_account_id)
