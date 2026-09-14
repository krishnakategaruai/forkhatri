"""The one shared, DB-backed rate limiter.

# [TR-CROSSCUT-02] ONE parameterised (scope, subject, window, limit) counter,
# called by report submission, activity creation and participation toggling —
# none builds its own counter "following the same pattern".
# Approach: a single atomic `INSERT ... ON CONFLICT DO UPDATE ... RETURNING
# attempt_count` on `milavn_platform.rate_limit_counter` (fixed windows aligned
# to epoch multiples), so N concurrent calls at the boundary admit exactly
# `limit_max`. Persistent, not in-memory: survives restarts, works across
# instances.
# Traces to: TR-CROSSCUT-02, MODULE-ARCHITECTURE-STANDARD §4c.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class RateLimitScope(StrEnum):
    REPORT_SUBMIT = "report_submit"  # TR41
    OCCURRENCE_CREATE = "occurrence_create"  # TR07
    PARTICIPATION_TOGGLE = "participation_toggle"  # TR12
    CIRCLE_CREATE = "circle_create"  # TR16
    MESSAGE_POST = "message_post"  # thread / board (beyond-MVP)
    PHOTO_UPLOAD = "photo_upload"  # moments (beyond-MVP)


@dataclass(frozen=True, slots=True)
class RateLimitResult:
    allowed: bool
    attempt_count: int
    limit_max: int
    window_start: datetime
    window_seconds: int

    @property
    def retry_after_seconds(self) -> int:
        reset_at = self.window_start + timedelta(seconds=self.window_seconds)
        return max(0, int((reset_at - datetime.now(UTC)).total_seconds()))


class RateLimitExceeded(Exception):
    def __init__(self, result: RateLimitResult) -> None:
        super().__init__(f"rate limit exceeded: {result.attempt_count}/{result.limit_max}")
        self.result = result


_UPSERT = text(
    """
    INSERT INTO milavn_platform.rate_limit_counter (rate_key, window_start, attempt_count, limit_max)
    VALUES (:key, :window_start, 1, :limit_max)
    ON CONFLICT (rate_key, window_start)
    DO UPDATE SET attempt_count = milavn_platform.rate_limit_counter.attempt_count + 1,
                  updated_at = now()
    RETURNING attempt_count
    """
)


def build_key(scope: RateLimitScope, subject: str) -> str:
    digest = hashlib.sha256(subject.strip().lower().encode("utf-8")).hexdigest()
    return f"{scope.value}:{digest}"


def _window_start(now: datetime, window_seconds: int) -> datetime:
    epoch = int(now.timestamp())
    return datetime.fromtimestamp(epoch - (epoch % window_seconds), tz=UTC)


async def enforce(
    session: AsyncSession,
    *,
    scope: RateLimitScope,
    subject: str,
    limit_max: int,
    window_seconds: int,
) -> RateLimitResult:
    now = datetime.now(UTC)
    window_start = _window_start(now, window_seconds)
    count: int = (
        await session.execute(
            _UPSERT,
            {"key": build_key(scope, subject), "window_start": window_start, "limit_max": limit_max},
        )
    ).scalar_one()
    result = RateLimitResult(count <= limit_max, count, limit_max, window_start, window_seconds)
    if not result.allowed:
        raise RateLimitExceeded(result)
    return result
