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
  * FR016 / TR016 — private family notes, forwarded only with approval.

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
from uuid import UUID, uuid4

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.components.authorization import interface as authz
from app.components.authorization.context import Action, GrantScope, GrantType
from app.components.home_circle.models import (
    HomeCircleNote,
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
    "MemberSummary",
    "NotFound",
    "PendingInvitationSummary",
    "PendingNoteSummary",
    "RateLimited",
    "accept_invitation",
    "decline_invitation",
    "forward_note",
    "get_membership_candidate",
    "invite",
    "leave",
    "SuggestionSummary",
    "list_home_circle",
    "list_notes",
    "list_pending_invitations",
    "list_pending_notes",
    "list_suggestions",
    "remove_member",
    "suggest",
    "write_note",
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


@dataclass(frozen=True, slots=True)
class PendingInvitationSummary:
    id: UUID
    candidate_account_id: UUID
    inviter_account_id: UUID
    relationship_type: RelationshipType
    created_at: datetime
    expires_at: datetime | None


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
    invitee_identifier: str,
    relationship_type: RelationshipType,
) -> UUID:
    """[FR007/TR007] Invite `invitee_identifier` (phone or email) into
    `candidate_account_id`'s Home Circle. Directory/username search does not
    exist in this codebase (confirmed against Identity Bridge — see
    `models.py`), so identifier is the only addressing scheme, exactly as
    TR007 itself names as the fallback.
    """
    # [SP007 denial-of-service row] Rate-limited per inviter, durable so a
    # rejected attempt (e.g. self-invite below) still counts — the same
    # reasoning Identity Bridge's own `enforce_durable()` calls document.
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

    inviter_phone, inviter_email = await identity.get_own_identifiers(
        session, account_id=inviter_account_id
    )
    if invitee_identifier in (inviter_phone, inviter_email):
        raise InviteSelf

    existing = (
        await session.execute(
            select(Invitation.id).where(
                Invitation.candidate_profile_id == candidate_account_id,
                Invitation.invitee_identifier == invitee_identifier,
                Invitation.status == InvitationStatus.PENDING,
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise AlreadyMember

    invitation_id = uuid4()
    await session.execute(
        text(
            """
            INSERT INTO mangaly_home_circle.invitation
                (id, candidate_profile_id, inviter_account_id, invitee_identifier,
                 relationship_type, status)
            VALUES (:id, :candidate, :inviter, :identifier, :relationship, 'pending')
            """
        ),
        {
            "id": invitation_id,
            "candidate": candidate_account_id,
            "inviter": inviter_account_id,
            "identifier": invitee_identifier,
            "relationship": relationship_type.value,
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
        },
    )
    return invitation_id


async def list_pending_invitations(
    session: AsyncSession, *, account_id: UUID
) -> list[PendingInvitationSummary]:
    """[FR008] The caller's own pending invitations — matched by identifier,
    not by `invitee_account_id` (which is NULL pre-response). Goes through
    the SECURITY DEFINER function from migration 006; see this module's
    docstring for why a plain SELECT cannot see these rows at all."""
    phone, email = await identity.get_own_identifiers(session, account_id=account_id)
    identifiers = [i for i in (phone, email) if i is not None]
    if not identifiers:
        return []

    rows = await session.execute(
        text(
            "SELECT id, candidate_profile_id, inviter_account_id, relationship_type, "
            "created_at, expires_at "
            "FROM mangaly_home_circle.list_pending_invitations_for_identifiers(:identifiers)"
        ),
        {"identifiers": identifiers},
    )
    return [
        PendingInvitationSummary(
            id=row.id,
            candidate_account_id=row.candidate_profile_id,
            inviter_account_id=row.inviter_account_id,
            relationship_type=RelationshipType(row.relationship_type),
            created_at=row.created_at,
            expires_at=row.expires_at,
        )
        for row in rows
    ]


async def _respond(
    session: AsyncSession, *, invitation_id: UUID, account_id: UUID, response: InvitationStatus
) -> tuple[UUID, RelationshipType]:
    phone, email = await identity.get_own_identifiers(session, account_id=account_id)
    identifiers = [i for i in (phone, email) if i is not None]
    row = (
        await session.execute(
            text(
                "SELECT candidate_profile_id, relationship_type "
                "FROM mangaly_home_circle.respond_to_invitation"
                "(:id, :account, :identifiers, :response)"
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
    return row.candidate_profile_id, RelationshipType(row.relationship_type)


async def accept_invitation(
    session: AsyncSession, *, invitation_id: UUID, account_id: UUID
) -> UUID:
    """[FR008/TR008] Accept: links the invitation, creates the membership,
    grants `family_info` scope, publishes `HomeCircleMemberJoined` — all in
    the caller's one transaction (TR069's outbox rule)."""
    candidate_account_id, relationship_type = await _respond(
        session,
        invitation_id=invitation_id,
        account_id=account_id,
        response=InvitationStatus.ACCEPTED,
    )

    membership_id = uuid4()
    await session.execute(
        text(
            """
            INSERT INTO mangaly_home_circle.membership
                (id, candidate_profile_id, member_account_id, invitation_id,
                 relationship_type, status)
            VALUES (:id, :candidate, :member, :invitation, :relationship, 'active')
            """
        ),
        {
            "id": membership_id,
            "candidate": candidate_account_id,
            "member": account_id,
            "invitation": invitation_id,
            "relationship": relationship_type.value,
        },
    )

    await authz.grant(
        session,
        subject_id=account_id,
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
            "member_account_id": str(account_id),
            "relationship_type": relationship_type.value,
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
    return suggestion_id


@dataclass(frozen=True, slots=True)
class SuggestionSummary:
    id: UUID
    suggested_profile_id: UUID
    suggested_by_relationship_type: RelationshipType
    note: str | None
    created_at: datetime


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
                       m.relationship_type
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
            note=row["note"],
            created_at=row["created_at"],
        )
        for row in rows
    ]


async def write_note(
    session: AsyncSession,
    *,
    member_account_id: UUID,
    membership_id: UUID,
    candidate_account_id: UUID,
    content: str,
) -> UUID:
    """[FR016] Family-only by default — `forwarded_at` stays NULL until the
    candidate explicitly approves forwarding this exact note.

    [TR017] Same chokepoint-binding requirement as `suggest()` — see its
    docstring; `hc_note_family_or_forwarded`'s family-side clause is gated
    on the same `has_scope()` call.
    """
    await authz.resolve(
        session,
        subject_id=member_account_id,
        account_id=member_account_id,
        target_profile_id=candidate_account_id,
        action=Action.WRITE,
    )

    note_id = uuid4()
    await session.execute(
        text(
            """
            INSERT INTO mangaly_home_circle.home_circle_note
                (id, candidate_profile_id, author_membership_id, content)
            VALUES (:id, :candidate, :membership, :content)
            """
        ),
        {
            "id": note_id,
            "candidate": candidate_account_id,
            "membership": membership_id,
            "content": content,
        },
    )
    return note_id


async def list_notes(
    session: AsyncSession, *, caller_account_id: UUID, candidate_account_id: UUID
) -> list[HomeCircleNote]:
    """Every note visible to the caller under RLS — family members see all
    of a candidate's notes (their own and siblings'/parents'), the candidate
    sees only notes already forwarded to them. The distinction is entirely
    the database policy's; this function does not re-derive it. A
    candidate's still-pending notes are NOT returned here at all — see
    `list_pending_notes()`, which surfaces only their existence, never their
    content, ahead of approval.

    [TR017] Binds the chokepoint the same way `suggest()`/`write_note()` do
    — needed whenever the caller is reading as family (`has_scope()`), a
    no-op in effect (but still the correct, single code path) when the
    caller is the candidate reading their own forwarded notes."""
    await authz.resolve(
        session,
        subject_id=caller_account_id,
        account_id=caller_account_id,
        target_profile_id=candidate_account_id,
        action=Action.READ,
    )
    rows = (
        await session.execute(
            select(HomeCircleNote)
            .where(HomeCircleNote.candidate_profile_id == candidate_account_id)
            .order_by(HomeCircleNote.created_at.desc())
        )
    ).scalars()
    return list(rows)


@dataclass(frozen=True, slots=True)
class PendingNoteSummary:
    id: UUID
    created_at: datetime


async def list_pending_notes(session: AsyncSession) -> list[PendingNoteSummary]:
    """[FR016] The calling candidate's own not-yet-forwarded notes — id and
    timestamp only, never content or author, so approving one is a genuinely
    blind trust decision rather than a preview that defeats the approval
    gate. Goes through `list_own_pending_notes()` (migration 007): a plain
    SELECT here returns nothing at all for the candidate, since
    `hc_note_family_or_forwarded` hides an unforwarded note from everyone
    except the family members who authored it."""
    rows = await session.execute(
        text("SELECT id, created_at FROM mangaly_home_circle.list_own_pending_notes()")
    )
    return [PendingNoteSummary(id=row.id, created_at=row.created_at) for row in rows]


async def forward_note(session: AsyncSession, *, note_id: UUID) -> None:
    """[FR016] The calling candidate approves forwarding ONE specific note
    to themselves — never the author, and never any other family member.

    Goes through `approve_note_forward()` (migration 008): a plain UPDATE
    here would be authorized by `hc_note_family_or_forwarded`'s
    `has_scope(candidate,'family_info')` clause for any family member too
    (Postgres derives `FOR ALL`'s `WITH CHECK` from `USING` when none is
    given), so the database's own RLS is not narrow enough by itself — the
    SECURITY DEFINER function re-checks `candidate_profile_id` against the
    caller's own `mangaly.account_id` internally, which is what actually
    makes this candidate-only.
    """
    approved = (
        await session.execute(
            text("SELECT mangaly_home_circle.approve_note_forward(:note_id)"),
            {"note_id": note_id},
        )
    ).scalar_one_or_none()
    if not approved:
        raise NotFound
