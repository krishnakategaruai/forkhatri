# [Trust pack, 2026-09-30] The hourly trust pass, run from main.py's
# scheduled loop and, in development, from `runTrustPass`.
#   * profession rules cache refresh (a council rule edited in the DB applies within the hour);
#   * promotions on a profile that now falls under a no-advertising rule are
#     cancelled (a member who adds "Legal services" to a promoted profile),
#     with a history row and a notice to the owner;
#   * "paid on time" questions opened for the payees now due;
#   * "N applicants still waiting" nudges to posters, once a week per post;
#   * council-verified entries whose year is up become `expired`.
# Each part is independent: one failing never stops the others.
# Traces to: VISION-2040 items 2-5
from __future__ import annotations

import logging

import asyncpg
from pydantic import BaseModel

from app.config import get_settings

logger = logging.getLogger(__name__)


class TrustPassOut(BaseModel):
    promotions_cancelled: int = 0
    paid_on_time_asked: int = 0
    applicants_waiting_nudged: int = 0
    credentials_expired: int = 0


async def cancel_restricted_promotions(conn: asyncpg.Connection) -> int:
    from app.notifications import notify_member

    # migration 028's narrow function: cancels and writes the order history
    rows = await conn.fetch("SELECT * FROM vyapar_commercial.cancel_profession_restricted_promotions()")
    for r in rows:
        await notify_member(conn, member_id=r["owner_id"], template="promotionCancelledProfession", link=f"/promotions/{r['promotion_id']}",
                            idempotency_key=f"promotion_cancelled_profession:{r['promotion_id']}")
    return len(rows)


async def run_trust_pass(pool: asyncpg.Pool) -> dict:
    from app.services import close_loop, credentials, paid_on_time
    from app.services.profession_rules import refresh_profession_rules

    out = TrustPassOut()
    try:
        await refresh_profession_rules(pool)
    except Exception:
        logger.exception("profession rules refresh failed")
    try:
        async with pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute("SELECT set_config('vyapar.service_role', 'dispatcher', true)")
                await conn.execute("SELECT set_config('vyapar.authz_context', $1, true)", get_settings().dispatcher_operator_member_id)
                out.promotions_cancelled = await cancel_restricted_promotions(conn)
                out.credentials_expired = await credentials.run_credential_expiry(conn)
    except Exception:
        logger.exception("trust pass: promotions/credentials part failed")
    try:
        out.paid_on_time_asked = (await paid_on_time.run_paid_on_time_pass(pool))["asked"]
    except Exception:
        logger.exception("trust pass: paid-on-time part failed")
    try:
        out.applicants_waiting_nudged = (await close_loop.run_waiting_nudge_pass(pool))["nudged"]
    except Exception:
        logger.exception("trust pass: applicants-waiting part failed")
    return out.model_dump()
