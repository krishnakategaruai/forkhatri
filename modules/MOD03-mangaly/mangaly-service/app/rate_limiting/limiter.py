"""The one shared, DB-backed rate limiter.

# [TR037/SP037] ONE parameterized (key, window, limit) counter. TR037 (verifier
# invites), TR093 (login failures) and TR095 (OTP resend) all call this exact
# implementation — none builds its own counter "following the same pattern".
# Approach: TR037 is the canonical statement, and `/MODULE-ARCHITECTURE-STANDARD.md`
# §4c exists because a Tech Reqs review caught three components each about to
# build their own copy. So this module exposes exactly one public function,
# `check_and_increment()`, and the per-caller differences (key prefix, window,
# limit) are arguments, not separate implementations.
#
# Two properties SP037 calls out specifically:
#   * **Atomic**, not read-then-write. SP037's caution is explicit: '"DB-backed"
#     alone doesn't guarantee atomicity — a naive read-then-write under
#     concurrent requests reintroduces exactly the race a rate limiter exists to
#     prevent.' The check is therefore a single `INSERT ... ON CONFLICT
#     (rate_limit_key, window_start) DO UPDATE SET hit_count = ... + 1
#     RETURNING hit_count`: one statement, one row lock, and the returned count
#     is the caller's own position in the window. N concurrent calls at the
#     boundary let through exactly `limit_max`.
#   * **Persistent**, not in-memory — it survives a process restart and works
#     across instances, which SP037 names as the property an in-memory or
#     per-component counter cannot give.
#
# Window model: fixed windows, aligned to epoch multiples of `window_seconds`.
# Chosen over a sliding log because `mangaly_platform.rate_limit_counter`'s
# already-applied schema is `UNIQUE (rate_limit_key, window_start)` — one row
# per window — and a sliding log would need a different table. Fixed windows
# admit up to 2x the limit across a boundary; that is acceptable for the three
# abuse cases here (invite spam, login brute force, SMS bombing), all of which
# are about cost and volume rather than a hard correctness bound.
#
# `rate_limit_counter` deliberately has no RLS: two of its three callers key on
# a pre-authentication identifier, where no `mangaly.account_id` exists yet to
# enforce a policy against (SP102's caution records this as a deliberate
# difference from `idempotency_key`, not an oversight).
# Traces to: TR037, TR093, TR095, SP037, SP093, SP095,
#            MODULE-ARCHITECTURE-STANDARD §4c.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class RateLimitScope(StrEnum):
    """The key prefixes in use. A new caller adds a member here rather than
    passing a free-text prefix, so every key in the table is greppable to a
    named requirement."""

    VERIFIER_INVITE = "verifier_invite"  # TR037
    LOGIN_FAILURE = "login_failure"  # TR093
    OTP_RESEND = "otp_resend"  # TR095
    OTP_VERIFY_ATTEMPT = "otp_verify_attempt"  # TR095 / SP095 brute-force bound
    SIGNUP = "signup"  # SP092 denial-of-service row
    PASSWORD_RESET_REQUEST = "password_reset_request"  # SP094 denial-of-service row
    LOGIN_OTP_REQUEST = "login_otp_request"  # DEC-V1-012 — OTP-primary login
    HOME_CIRCLE_INVITE = "home_circle_invite"  # TR007/SP007
    CONNECTION_REQUEST = "connection_request"  # SP042 — flagged gap, not in TR042 itself
    MESSAGE_SEND = "message_send"  # SP049 — flagged gap, not in TR049 itself


@dataclass(frozen=True, slots=True)
class RateLimitResult:
    allowed: bool
    hit_count: int
    limit_max: int
    window_start: datetime
    window_seconds: int

    @property
    def retry_after_seconds(self) -> int:
        reset_at = self.window_start + timedelta(seconds=self.window_seconds)
        return max(0, int((reset_at - datetime.now(UTC)).total_seconds()))


class RateLimitExceeded(Exception):
    """Raised by `enforce()`. Carries the result so a handler can set Retry-After."""

    def __init__(self, result: RateLimitResult) -> None:
        super().__init__(
            f"rate limit exceeded: {result.hit_count}/{result.limit_max} "
            f"in a {result.window_seconds}s window"
        )
        self.result = result


# One statement. `hit_count` on conflict is incremented from the stored value,
# so the RETURNING value is this caller's own ordinal within the window.
_UPSERT_SQL = text(
    """
    INSERT INTO mangaly_platform.rate_limit_counter
        (rate_limit_key, window_start, window_seconds, hit_count, limit_max)
    VALUES (:key, :window_start, :window_seconds, 1, :limit_max)
    ON CONFLICT (rate_limit_key, window_start)
    DO UPDATE SET hit_count = mangaly_platform.rate_limit_counter.hit_count + 1
    RETURNING hit_count
    """
)

_PEEK_SQL = text(
    """
    SELECT hit_count FROM mangaly_platform.rate_limit_counter
    WHERE rate_limit_key = :key AND window_start = :window_start
    """
)


def build_key(scope: RateLimitScope, subject: str) -> str:
    """Compose a rate-limit key.

    The subject is hashed for the pre-authentication scopes' benefit: the login,
    OTP and reset limiters key on a raw phone number or email address, and
    storing those in plaintext in an infrastructure table would put identifiers
    in a table with no RLS on it (SP104's concentration-risk concern). A stable
    SHA-256 keeps the counter functional while the table holds no readable PII.
    """
    digest = hashlib.sha256(subject.strip().lower().encode("utf-8")).hexdigest()
    return f"{scope.value}:{digest}"


def _window_start(now: datetime, window_seconds: int) -> datetime:
    epoch_seconds = int(now.timestamp())
    aligned = epoch_seconds - (epoch_seconds % window_seconds)
    return datetime.fromtimestamp(aligned, tz=UTC)


async def check_and_increment(
    session: AsyncSession,
    *,
    scope: RateLimitScope,
    subject: str,
    limit_max: int,
    window_seconds: int,
    now: datetime | None = None,
) -> RateLimitResult:
    """Atomically record one hit and report whether the caller is within the limit.

    Increments unconditionally, including on the request that exceeds the limit —
    that is deliberate: an attacker who keeps hitting a blocked endpoint should
    keep extending their own window, and the hit count is also the signal
    Step 13 alerts on for credential-stuffing detection (SP093 repudiation row).
    """
    now = now or datetime.now(UTC)
    window_start = _window_start(now, window_seconds)
    key = build_key(scope, subject)

    result = await session.execute(
        _UPSERT_SQL,
        {
            "key": key,
            "window_start": window_start,
            "window_seconds": window_seconds,
            "limit_max": limit_max,
        },
    )
    hit_count: int = result.scalar_one()

    allowed = hit_count <= limit_max
    if not allowed:
        logger.warning("rate limit exceeded scope=%s hits=%s/%s", scope.value, hit_count, limit_max)
    return RateLimitResult(
        allowed=allowed,
        hit_count=hit_count,
        limit_max=limit_max,
        window_start=window_start,
        window_seconds=window_seconds,
    )


async def enforce(
    session: AsyncSession,
    *,
    scope: RateLimitScope,
    subject: str,
    limit_max: int,
    window_seconds: int,
    now: datetime | None = None,
) -> RateLimitResult:
    """`check_and_increment()` that raises instead of returning `allowed=False`."""
    result = await check_and_increment(
        session,
        scope=scope,
        subject=subject,
        limit_max=limit_max,
        window_seconds=window_seconds,
        now=now,
    )
    if not result.allowed:
        raise RateLimitExceeded(result)
    return result


async def peek(
    session: AsyncSession,
    *,
    scope: RateLimitScope,
    subject: str,
    window_seconds: int,
    now: datetime | None = None,
) -> int:
    """Read the current window's hit count without incrementing it.

    Needed by TR095's minimum-resend-interval check, which must not itself
    consume a slot from the hourly resend budget.
    """
    now = now or datetime.now(UTC)
    result = await session.execute(
        _PEEK_SQL,
        {"key": build_key(scope, subject), "window_start": _window_start(now, window_seconds)},
    )
    return int(result.scalar_one_or_none() or 0)


def constant_time_equals(left: str, right: str) -> bool:
    """Shared constant-time comparison for OTP codes and reset tokens (SP094)."""
    return hmac.compare_digest(left, right)


async def enforce_durable(
    *,
    scope: RateLimitScope,
    subject: str,
    limit_max: int,
    window_seconds: int,
    now: datetime | None = None,
) -> RateLimitResult:
    """`enforce()` on its OWN connection, so the count survives the caller's rollback.

    [TR093/SP093] Why this exists, found by running the real login path rather
    than by reading it:

    A failed login raises, the request transaction rolls back, and — if the
    counter was incremented inside that same transaction — the increment is
    rolled back with it. The counter therefore never reaches the limit, and the
    rate limiter cannot rate-limit failures, which is the only thing it exists
    to do. Verified live: eight consecutive bad logins produced eight 401s, zero
    429s, and zero `login_failure:` rows in `mangaly_platform.rate_limit_counter`.

    Counting an ATTEMPT is not part of the business transaction and must not
    share its fate, so this opens a short independent session, commits, and
    closes. Callers whose work should be rolled back together (a quota consumed
    only if the action succeeds) still want plain `enforce()` — the two are
    genuinely different requirements, not two spellings of one.

    `mangaly_platform.rate_limit_counter` carries no RLS and its keys are
    pre-authentication by design (SP102's note), so this needs no account
    context — which is also why it is safe to run outside the request's own
    authorization scope.
    """
    from app.db.engine import get_process_session_factory

    session_factory = get_process_session_factory()
    async with session_factory() as own_session, own_session.begin():
        return await enforce(
            own_session,
            scope=scope,
            subject=subject,
            limit_max=limit_max,
            window_seconds=window_seconds,
            now=now,
        )
