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
    "new_to_community": "New to the community",
}


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
) -> None:
    await session.execute(
        text(
            """
            INSERT INTO milavn_trust.feedback (occurrence_id, participant_member_id, rating_internal, comments_internal)
            VALUES (:o, :m, :r, NULLIF(:c, ''))
            ON CONFLICT (occurrence_id, participant_member_id) DO UPDATE
              SET rating_internal = EXCLUDED.rating_internal, comments_internal = EXCLUDED.comments_internal
            """
        ),
        {"o": str(occurrence_id), "m": str(member_id), "r": rating, "c": (comments or "").strip()},
    )
    # [FR067] Feeds reputation internally; [FR069] a positive rating adds a
    # signal, a low rating adds nothing automatic — a human decides.
    if rating is not None and rating >= 4:
        await record_signal(session, member_id=organizer_member_id, signal="community_contribution", occurrence_id=occurrence_id, weight=0.5)
