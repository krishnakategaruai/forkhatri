"""Trust & verification — the evidence behind a profile (M01-F, baseline §13).

Mangaly's whole thesis is that trust is EVIDENCE, NOT A SCORE (baseline §4.8,
§13.1). There is deliberately no trust score, no reputation ranking and no
public rating here, and there must never be one: this module answers "what has
actually been verified about this person, how, and when", and nothing else.

Verification does not certify character, safety, honesty or marital
suitability (§13.4) — it certifies a fact. Safety is a separate layer (§4.10):
a verified person can still behave badly.

Freshness matters. A fact that can change carries `freshness_expires_at`, and
an expired layer is NOT reported as verified — a stale claim presented as a
current one is worse than no claim, because it is trusted more.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# The six conceptual layers of §13.2, in the order they are worth showing:
# an identity check is more meaningful to a stranger than an account check.
LAYER_ORDER: tuple[str, ...] = (
    "identity_age",
    "community_verification",
    "operational_verification",
    "profile_facts",
    "home_circle_relationship",
    "account_authenticity",
)


@dataclass(frozen=True)
class VerifiedLayer:
    """One verified fact, with the provenance §13.4 requires."""

    layer: str
    verified_at: datetime | None
    provenance: str | None
    source_category: str | None


def _order(layer: str) -> int:
    return LAYER_ORDER.index(layer) if layer in LAYER_ORDER else len(LAYER_ORDER)


async def verified_layers_for(
    session: AsyncSession, *, account_ids: list[UUID]
) -> dict[UUID, list[VerifiedLayer]]:
    """Currently-verified layers for each account, most meaningful first.

    Goes through `mangaly_trust.verified_layers_for()` (migration 038), the
    narrow SECURITY DEFINER read that returns the non-identifying summary —
    layer, date, method — and never the free-text provenance. That is what
    makes it safe to show before a connection exists (§15.1), which is the
    only point at which evidence can actually inform the decision.

    Only `verified` counts. `self_reported` is not verification — presenting
    it as such would be the teaser-trust UX §8.1 forbids — and expired layers
    are excluded by the function itself (§13.4 freshness).
    """
    if not account_ids:
        return {}
    rows = (
        await session.execute(
            text(
                "SELECT account_id, layer, verified_at, source_category "
                "FROM mangaly_trust.verified_layers_for(CAST(:ids AS uuid[]))"
            ),
            {"ids": [str(a) for a in account_ids]},
        )
    ).mappings().all()

    out: dict[UUID, list[VerifiedLayer]] = {}
    for r in rows:
        out.setdefault(r["account_id"], []).append(
            VerifiedLayer(
                layer=r["layer"],
                verified_at=r["verified_at"],
                provenance=None,
                source_category=r["source_category"],
            )
        )
    for layers in out.values():
        layers.sort(key=lambda v: _order(v.layer))
    return out


def snapshot_form(layers: list[VerifiedLayer]) -> list[dict[str, str | None]]:
    """The compact form stored on the Discovery index snapshot.

    Discovery has to show evidence BEFORE a connection exists (§15.1: "Recipient
    can inspect available trust/evidence signals" before accepting), but the
    verification table's own RLS only admits the owner or a holder of
    `candidate_info`. The snapshot is the established pre-connection-safe
    surface — the same one `compatibility.explain()` reads — so the summary is
    written there when the candidate's own index is refreshed, in their own
    RLS context.

    Only the layer, the date and the method travel. No document, no identifier,
    no verifier's name: enough to judge the evidence, nothing that leaks a
    person (§8.1, privacy by design).
    """
    return [
        {
            "layer": v.layer,
            "verified_on": v.verified_at.astimezone(timezone.utc).date().isoformat()
            if v.verified_at
            else None,
            "method": v.source_category,
        }
        for v in layers
    ]


# ---------------------------------------------------------------------------
# Live face match (DEC-V1-016) — the only verification a member can earn
# themselves, and the gate a profile-maker must pass (DEC-V1-020 / DEC-V1-025).
#
# HOW IT WORKS, AND WHAT IT CANNOT PROVE. The camera, the liveness challenge
# and the face comparison all run in the member's browser
# (`mangaly-web/app/me/verify/`), and only the result — one distance number and
# whether the challenge passed — is posted here. That is a deliberate v1
# trade-off, and it must be read honestly: a client-side comparison CAN be
# tampered with. Anyone who edits the page's JavaScript or replays the request
# can send `distance = 0.1, liveness_passed = true` without ever facing a
# camera. What the server contributes is:
#   * the threshold is applied HERE, not trusted from the client, and it is
#     strict (below face-api's 0.6 default) so an honest-but-borderline match
#     fails rather than passes (DEC-V1-016: false accept is the safety failure);
#   * attempts are rate-limited per account, so the threshold cannot be probed;
#   * the consent is recorded server-side and the outcome is revocable;
#   * a failed or doubted result is meant to route to human review — the
#     `admin_verification_request` queue exists, the Operations surface that
#     would work it does not yet, so today the member is told to retry or ask
#     support; and a
#     report about a verified profile is weighed against a badge that says
#     exactly what it is — "photos confirmed as you", a method and a date.
# Doing the comparison server-side would mean uploading face frames or
# embeddings, i.e. holding biometric data, which DEC-V1-016 refuses; a
# vendor's passive-liveness SDK is out of scope by the same decision. The next
# step up, if tampering is ever seen, is server-side verification of a signed
# on-device attestation — not storing faces.
#
# NOTHING BIOMETRIC IS STORED OR RETURNED. The distance is an internal
# threshold input, like a spam filter's; it is never written anywhere and never
# echoed back. The member sees pass/fail with a date (§3, §4.8, §11.3).
# ---------------------------------------------------------------------------

# face-api.js documents 0.6 (Euclidean, 128-d descriptors) as its same-person
# threshold. Mangaly sits well below it: a false accept attaches a confirming
# badge to someone else's photos, a false reject costs a retry in better light.
FACE_MATCH_THRESHOLD = 0.45

# Which consent wording the person agreed to. Bump when `verify:consent.*`
# changes meaning, so the log shows exactly what each person saw.
FACE_MATCH_NOTICE_VERSION = "2026-09-22"

# Ten attempts a day is plenty for bad light and a wobbly phone, and far too
# few to walk the threshold.
FACE_MATCH_ATTEMPTS_PER_DAY = 10


@dataclass(frozen=True)
class FaceMatchStatus:
    has_profile: bool
    verified: bool
    verified_at: datetime | None
    expires_at: datetime | None
    consent_at: datetime | None


class NoPhotosToCompare(Exception):
    """The caller has no profile, so no photos of themselves to compare with."""


class FaceMatchRateLimited(Exception):
    def __init__(self, retry_after_seconds: int) -> None:
        super().__init__("face match attempts exhausted")
        self.retry_after_seconds = retry_after_seconds


async def face_match_status(session: AsyncSession, *, account_id: UUID) -> FaceMatchStatus:
    """The caller's own face-match state (migration 045; self only)."""
    row = (
        await session.execute(
            text("SELECT * FROM mangaly_trust.face_match_status(:me)"), {"me": account_id}
        )
    ).mappings().one()
    return FaceMatchStatus(
        has_profile=row["has_profile"],
        verified=row["verified"],
        verified_at=row["verified_at"],
        expires_at=row["expires_at"],
        consent_at=row["consent_at"],
    )


async def is_face_verified(session: AsyncSession, *, account_id: UUID) -> bool:
    """True when the caller holds a current (unexpired) face match."""
    return (await face_match_status(session, account_id=account_id)).verified


def face_match_passes(*, distance: float, liveness_passed: bool, photos_compared: int) -> bool:
    """The server's decision. `distance` is the WORST photo's best-face distance
    the browser measured, so every compared photo must contain this person."""
    return (
        liveness_passed
        and photos_compared >= 1
        and 0.0 <= distance < FACE_MATCH_THRESHOLD
    )


async def record_face_match(
    session: AsyncSession,
    *,
    account_id: UUID,
    distance: float,
    liveness_passed: bool,
    photos_compared: int,
    photos_on_profile: int,
) -> tuple[bool, FaceMatchStatus]:
    """Apply the threshold and record the outcome for the caller.

    The attempt is counted on its own connection (`enforce_durable`) so a
    failure cannot roll its own count back. `photos_compared` may not exceed
    the photos the member actually has — a client claiming to have compared
    photos that do not exist is not believed."""
    from app.rate_limiting import limiter

    try:
        await limiter.enforce_durable(
            scope=limiter.RateLimitScope.FACE_MATCH_ATTEMPT,
            subject=str(account_id),
            limit_max=FACE_MATCH_ATTEMPTS_PER_DAY,
            window_seconds=86400,
        )
    except limiter.RateLimitExceeded as exc:
        raise FaceMatchRateLimited(exc.result.retry_after_seconds) from exc

    if photos_on_profile < 1:
        raise NoPhotosToCompare
    passed = photos_compared <= photos_on_profile and face_match_passes(
        distance=distance, liveness_passed=liveness_passed, photos_compared=photos_compared
    )
    try:
        await session.execute(
            text("SELECT * FROM mangaly_trust.record_face_match(:me, :passed, :notice)"),
            {"me": account_id, "passed": passed, "notice": FACE_MATCH_NOTICE_VERSION},
        )
    except Exception as exc:  # asyncpg's MG045 surfaces wrapped by SQLAlchemy
        if "MG045" in str(getattr(exc, "orig", exc)) or "no profile photos" in str(exc):
            raise NoPhotosToCompare from exc
        raise
    return passed, await face_match_status(session, account_id=account_id)


async def withdraw_face_match(session: AsyncSession, *, account_id: UUID) -> None:
    """Consent ends (stamped, kept as the audit record) and the verification it
    supported is deleted."""
    await session.execute(
        text("SELECT mangaly_trust.withdraw_face_match(:me)"), {"me": account_id}
    )
