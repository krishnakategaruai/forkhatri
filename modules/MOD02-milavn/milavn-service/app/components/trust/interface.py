"""Trust & Reputation (incl. Feedback) — public interface (`milavn_trust`).

# [FR030-FR037, FR066-FR069, TR25-TR28, TR44] Every subject resolves to
# exactly one visible trust level; reputation is computed from named
# behaviours, surfaced ONLY as qualitative labels (never a score, never
# purchasable), and a single no-show/feedback never triggers a penalty.
# Approach: `trust_status` rows are written through the definer-owned
# `ensure_default_trust`; reputation signals are appended through
# `record_signal` and read back only via `reputation_labels()` — there is no
# function here that returns the numeric weight. Feedback is optional
# (skippable), internal-only, and only ever *adds* a positive signal for the
# organizer when the rating is high; low ratings are stored for a human
# moderator to consider, never auto-acted on (FR069).
# Traces to: TR25, TR26, TR27, TR28, TR44, TR15.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

TRUST_LABELS = {
    "forkhatri_verified": "ForKhatri Verified",
    "community_verified": "Community Verified",
    "partner_verified": "Partner Verified",
    "external_trusted_source": "Trusted Source",
    "community_submitted": "Community Submitted",
}
POSITIVE_TRUST = {"forkhatri_verified", "community_verified", "partner_verified", "external_trusted_source"}

REPUTATION_LABELS = {
    "identity_verified": "Identity verified",
    "experienced_organizer": "Experienced organizer",
    "has_hosted": "Has hosted before",
    "reliable_attendee": "Reliable attendee",
    "community_contributor": "Community contributor",
    "appreciated_host": "Appreciated host",
    "new_to_community": "New to the community",
}
COME_AGAIN = ("yes", "maybe", "no")


@dataclass(frozen=True, slots=True)
class TrustBadge:
    level: str
    label: str
    positive: bool


async def trust_for(session: AsyncSession, *, subject_type: str, subject_id: UUID) -> TrustBadge:
    row = (
        await session.execute(
            text("SELECT trust_level::text FROM milavn_trust.trust_status WHERE subject_type = CAST(:t AS milavn_trust.trust_subject_type) AND subject_id = :s"),
            {"t": subject_type, "s": str(subject_id)},
        )
    ).first()
    level = row[0] if row else "community_submitted"
    return TrustBadge(level, TRUST_LABELS[level], level in POSITIVE_TRUST)


async def trust_for_many(session: AsyncSession, *, subject_type: str, subject_ids: list[UUID]) -> dict[UUID, TrustBadge]:
    if not subject_ids:
        return {}
    rows = (
        await session.execute(
            text(
                "SELECT subject_id, trust_level::text FROM milavn_trust.trust_status "
                "WHERE subject_type = CAST(:t AS milavn_trust.trust_subject_type) AND subject_id = ANY(:ids)"
            ),
            {"t": subject_type, "ids": [str(s) for s in subject_ids]},
        )
    ).all()
    found = {r.subject_id: r[1] for r in rows}
    return {sid: TrustBadge(lvl, TRUST_LABELS[lvl], lvl in POSITIVE_TRUST) for sid in subject_ids for lvl in [found.get(sid, "community_submitted")]}


async def resolve_organizer_level(session: AsyncSession, *, member_id: UUID, identity_level: int) -> str:
    """[FR030] Deterministic: platform-verified identity wins, then track record, else submitted."""
    if identity_level >= 2:
        return "forkhatri_verified"
    labels = await reputation_labels(session, member_id=member_id)
    if "experienced_organizer" in labels or "has_hosted" in labels:
        return "community_verified"
    return "community_submitted"


async def ensure_trust(session: AsyncSession, *, subject_type: str, subject_id: UUID, level: str) -> None:
    await session.execute(
        text("SELECT milavn_trust.ensure_default_trust(:t, :s, :l)"),
        {"t": subject_type, "s": str(subject_id), "l": level},
    )


async def set_trust(session: AsyncSession, *, subject_type: str, subject_id: UUID, level: str) -> None:
    await session.execute(
        text(
            """
            INSERT INTO milavn_trust.trust_status (subject_type, subject_id, trust_level)
            VALUES (CAST(:t AS milavn_trust.trust_subject_type), :s, CAST(:l AS milavn_trust.trust_level))
            ON CONFLICT (subject_type, subject_id) DO UPDATE SET trust_level = EXCLUDED.trust_level, updated_at = now()
            """
        ),
        {"t": subject_type, "s": str(subject_id), "l": level},
    )


async def reputation_labels(session: AsyncSession, *, member_id: UUID) -> list[str]:
    """[FR037] Qualitative only — the raw score is unreachable from a request."""
    row = (await session.execute(text("SELECT milavn_trust.reputation_labels(:m)"), {"m": str(member_id)})).scalar_one()
    return list(row or [])


def label_text(labels: list[str]) -> list[str]:
    """[FR002/FR037] Qualitative labels, in the person's language; English dict is the fallback."""
    from app.i18n import current_language, translate

    lang = current_language.get()
    out = []
    for lbl in labels:
        key = f"reputation.{lbl}"
        txt = translate(key, lang)
        out.append(REPUTATION_LABELS.get(lbl, lbl) if txt == key else txt)
    return out


async def record_signal(session: AsyncSession, *, member_id: UUID, signal: str, occurrence_id: UUID | None, weight: float) -> None:
    """[FR034] Named behaviours only. Never called from a payment path (FR036)."""
    await session.execute(
        text("SELECT milavn_trust.record_signal(:m, :s, :o, :w)"),
        {"m": str(member_id), "s": signal, "o": str(occurrence_id) if occurrence_id else None, "w": weight},
    )


# --- Feedback (FR066-FR069) -------------------------------------------------


class FeedbackNotAllowed(Exception):
    pass


async def feedback_exists(session: AsyncSession, *, occurrence_id: UUID, member_id: UUID) -> bool:
    row = (
        await session.execute(
            text("SELECT 1 FROM milavn_trust.feedback WHERE occurrence_id = :o AND participant_member_id = :m"),
            {"o": str(occurrence_id), "m": str(member_id)},
        )
    ).first()
    return row is not None


async def submit_feedback(
    session: AsyncSession,
    *,
    occurrence_id: UUID,
    member_id: UUID,
    organizer_member_id: UUID,
    rating: int | None,
    comments: str | None,
    come_again: str | None = None,
) -> None:
    """[FR066-FR069, FR107] One private question — "Would you come again?" — plus an optional line. Nobody but
    a moderator ever reads an individual answer; the host sees counts only."""
    if come_again is not None and come_again not in COME_AGAIN:
        raise FeedbackNotAllowed(come_again)
    await session.execute(
        text(
            """
            INSERT INTO milavn_trust.feedback (occurrence_id, participant_member_id, rating_internal, comments_internal, come_again)
            VALUES (:o, :m, :r, NULLIF(:c, ''), :ca)
            ON CONFLICT (occurrence_id, participant_member_id) DO UPDATE
              SET rating_internal = EXCLUDED.rating_internal, comments_internal = EXCLUDED.comments_internal, come_again = EXCLUDED.come_again
            """
        ),
        {"o": str(occurrence_id), "m": str(member_id), "r": rating, "c": (comments or "").strip(), "ca": come_again},
    )
    # [FR067] Feeds reputation internally; [FR069] a positive answer adds a
    # signal, a negative one adds nothing automatic — a human decides.
    if come_again == "yes" or (rating is not None and rating >= 4):
        await record_signal(session, member_id=organizer_member_id, signal="community_contribution", occurrence_id=occurrence_id, weight=0.5)


# --- Thanks (FR107) -------------------------------------------------------------


class InvalidThanks(Exception):
    pass


async def give_thanks(session: AsyncSession, *, occurrence_id: UUID, member_id: UUID, host_member_id: UUID, message: str) -> bool:
    """One thank-you per attendee per activity (editable). Returns True the first time, so the host is told once."""
    msg = (message or "").strip()
    if not 1 <= len(msg) <= 140 or member_id == host_member_id:
        raise InvalidThanks
    inserted = (
        await session.execute(
            text(
                "INSERT INTO milavn_trust.thanks (occurrence_id, from_member_id, to_member_id, message) VALUES (:o, :f, :t, :m) "
                "ON CONFLICT (occurrence_id, from_member_id) DO UPDATE SET message = EXCLUDED.message RETURNING (xmax = 0)"
            ),
            {"o": str(occurrence_id), "f": str(member_id), "t": str(host_member_id), "m": msg},
        )
    ).scalar_one()
    if inserted:
        from app.events import bus

        await bus.publish(
            session,
            schema="milavn_trust",
            event_type="thanks.given",
            aggregate_id=occurrence_id,
            payload={"occurrence_id": occurrence_id, "from_member_id": member_id, "to_member_id": host_member_id},
        )
    return bool(inserted)


async def has_thanked(session: AsyncSession, *, occurrence_id: UUID, member_id: UUID) -> bool:
    row = (
        await session.execute(text("SELECT 1 FROM milavn_trust.thanks WHERE occurrence_id = :o AND from_member_id = :m"), {"o": str(occurrence_id), "m": str(member_id)})
    ).first()
    return row is not None


async def thanks_received(session: AsyncSession, *, occurrence_id: UUID) -> list[tuple[UUID, str]]:
    """The host's own thank-you notes for this activity (RLS: only the sender and the host can read a note)."""
    rows = (
        await session.execute(text("SELECT from_member_id, message FROM milavn_trust.thanks WHERE occurrence_id = :o ORDER BY created_at"), {"o": str(occurrence_id)})
    ).all()
    return [(r[0], r[1]) for r in rows]
