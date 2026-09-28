"""Recalculate every stored kundli after a horoscope rules or provider update.

A match is refused for charts made under another rules version (by design:
results from different rules are never mixed). After the horoscope service's
RULES_VERSION changes, run this once: it rebuilds each chart from the
person's saved birth details and adds it as the new current chart. Old rows
stay, append-only, so earlier results remain explainable.

Needs the horoscope service running. Run: python -m scripts.recalculate_horoscope_charts
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.ext.asyncio import create_async_engine  # noqa: E402

from app.components.horoscope.interface import _birth_details  # noqa: E402
from app.components.profile.models import FieldState  # noqa: E402
from app.config.settings import get_settings  # noqa: E402

_OWNER_URL = "postgresql+asyncpg://mangaly_owner:mangaly_owner_dev_password@localhost:5433/mangaly"


async def main() -> None:
    settings = get_settings()
    engine = create_async_engine(_OWNER_URL)
    done = skipped = 0
    async with engine.begin() as conn, httpx.AsyncClient(timeout=15) as client:
        people = (
            await conn.execute(
                text(
                    "SELECT DISTINCT c.account_id, p.id, p.date_of_birth FROM mangaly_horoscope.chart c "
                    "JOIN mangaly_profile.profile p ON p.account_id = c.account_id"
                )
            )
        ).all()
        for account_id, profile_id, dob in people:
            rows = (
                await conn.execute(
                    text(
                        "SELECT attribute_key, state::text, value FROM mangaly_profile.profile_attribute "
                        "WHERE profile_id = :p AND category = 'horoscope'"
                    ),
                    {"p": profile_id},
                )
            ).all()
            attrs = {k: (FieldState(s), v) for k, s, v in rows}
            details = _birth_details(dob.isoformat(), attrs)
            if details is None:
                skipped += 1
                continue
            res = await client.post(
                f"{settings.horoscope_service_url}/horoscope/calculate/chart",
                json={"birthDetails": details},
                headers={"authorization": f"Bearer {settings.horoscope_service_token}", "x-mangaly-viewer": "maintenance"},
            )
            res.raise_for_status()
            chart = res.json()
            await conn.execute(
                text(
                    """
                    INSERT INTO mangaly_horoscope.chart
                        (account_id, calculation_id, calculation_version, rules_version, provider,
                         rashi, nakshatra, moon_sign_half, mangal_status, mangal_level, chart)
                    VALUES (:a, :c, :cv, :rv, :pr, :r, :n, :h, :ms, :ml, CAST(:chart AS jsonb))
                    ON CONFLICT (account_id, calculation_id) DO NOTHING
                    """
                ),
                {
                    "a": account_id, "c": chart["calculationId"], "cv": chart["calculationVersion"],
                    "rv": chart["rulesVersion"], "pr": f"{chart['provider']['name']}@{chart['provider']['version']}",
                    "r": chart["moon"]["rashi"], "n": chart["moon"]["nakshatra"], "h": chart.get("moonSignHalf"),
                    "ms": chart["mangal"]["status"], "ml": chart["mangal"]["level"], "chart": json.dumps(chart),
                },
            )
            done += 1
    await engine.dispose()
    print(f"recalculated {done} charts, skipped {skipped} (no place of birth chosen)")


if __name__ == "__main__":
    asyncio.run(main())
