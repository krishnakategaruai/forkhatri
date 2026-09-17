"""Shared fixed-window rate limiter (MODULE-ARCHITECTURE-STANDARD §4c, TR20).

Each hit is counted in its own short transaction so it survives even when the
request that caused it fails and rolls back; otherwise failed password guesses
would never count toward the limit.
"""

from __future__ import annotations

import secrets
from datetime import UTC, datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class RateLimitExceeded(Exception):
    def __init__(self, retry_after_seconds: int) -> None:
        super().__init__(f"rate limited for {retry_after_seconds}s")
        self.retry_after_seconds = max(1, retry_after_seconds)


async def hit(
    factory: async_sessionmaker[AsyncSession], key: str, *, limit: int, window_seconds: int
) -> None:
    now_epoch = int(datetime.now(UTC).timestamp())
    start_epoch = now_epoch - now_epoch % window_seconds
    async with factory() as session, session.begin():
        count = await session.scalar(
            text(
                "INSERT INTO platform.rate_limit_counter (bucket_key, window_start, hit_count) "
                "VALUES (:key, :window_start, 1) "
                "ON CONFLICT (bucket_key, window_start) "
                "DO UPDATE SET hit_count = platform.rate_limit_counter.hit_count + 1 "
                "RETURNING hit_count"
            ),
            {"key": key, "window_start": datetime.fromtimestamp(start_epoch, UTC)},
        )
        if secrets.randbelow(200) == 0:
            await session.execute(
                text("DELETE FROM platform.rate_limit_counter WHERE window_start < now() - interval '1 day'")
            )
    if count is not None and count > limit:
        raise RateLimitExceeded(start_epoch + window_seconds - now_epoch)
