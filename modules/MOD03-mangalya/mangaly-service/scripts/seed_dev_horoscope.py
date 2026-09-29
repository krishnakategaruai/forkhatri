"""Development seed: birth details and kundlis for some seeded candidates.

Horoscope matching needs both people's time and place of birth. This fills
them for a handful of seeded candidates — deliberately mixed: exact times,
times known to within 30 minutes or an hour, one unknown time, one born
abroad — the same way `seed_dev_profile_depth.py` fills other sections, and
then asks the real horoscope service for each chart so the profile screens and
the Discover filter show real results. The owner's own account is never
touched.

Needs the horoscope service running (npm run dev, or `npm run dev` in
modules/MOD03-mangaly/horoscope-service).

Run: python -m scripts.seed_dev_horoscope
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
from app.components.places import interface as places  # noqa: E402
from app.components.profile.models import FieldState  # noqa: E402
from app.config.settings import get_settings  # noqa: E402

_OWNER_URL = "postgresql+asyncpg://mangaly_owner:mangaly_owner_dev_password@localhost:5433/mangaly"

# name -> (birth time, how sure, place searched for)
SEED: dict[str, tuple[str | None, str, str]] = {
    "Rahul Varma": ("05:42", "exact", "Bengaluru"),
    "Aravind Krishnan": ("21:15", "exact", "Chennai"),
    "Harsha Vardhan": ("09:30", "about_30", "Vijayawada"),
    "Kunal Bhasin": ("14:05", "exact", "Hyderabad"),
    "Naveen Shetty": ("03:50", "about_60", "Mangaluru"),
    "Vishnu Teja": ("18:20", "exact", "Visakhapatnam"),
    "Siddharth Reddy": (None, "unknown", "Guntur"),
    "Ishaan Dhawan": ("11:10", "exact", "London"),
    "Kavya Rao": ("07:25", "exact", "Hyderabad"),
    "Ananya Reddy": ("16:40", "about_15", "Warangal"),
}


async def main() -> None:
    settings = get_settings()
    engine = create_async_engine(_OWNER_URL)
    async with engine.begin() as conn, httpx.AsyncClient(timeout=15) as client:
        for name, (time, accuracy, place_query) in SEED.items():
            row = (
                await conn.execute(
                    text("SELECT id, account_id, date_of_birth FROM mangaly_profile.profile WHERE name = :n"), {"n": name}
                )
            ).first()
            if row is None:
                print(f"skip {name}: no profile")
                continue
            profile_id, account_id, dob = row
            place = places.search(place_query)[0]
            values = {
                "birth_time": time,
                "birth_time_accuracy": accuracy,
                "birth_place": place.label,
                "birth_place_geo": place.to_geo(),
            }
            for key, value in values.items():
                state = "value" if value is not None else "declined"
                await conn.execute(
                    text(
                        """
                        INSERT INTO mangaly_profile.profile_attribute (id, profile_id, category, attribute_key, state, value)
                        VALUES (gen_random_uuid(), :p, 'horoscope', :k, CAST(:s AS mangaly_profile.field_state), CAST(:v AS jsonb))
                        ON CONFLICT (profile_id, category, attribute_key)
                        DO UPDATE SET state = EXCLUDED.state, value = EXCLUDED.value, updated_at = now()
                        """
                    ),
                    {"p": profile_id, "k": key, "s": state, "v": json.dumps(value) if value is not None else None},
                )
            attrs = {k: (FieldState.VALUE if v is not None else FieldState.DECLINED, v) for k, v in values.items()}
            details = _birth_details(dob.isoformat(), attrs)
            res = await client.post(
                f"{settings.horoscope_service_url}/horoscope/calculate/chart",
                json={"birthDetails": details},
                headers={"authorization": f"Bearer {settings.horoscope_service_token}", "x-mangaly-viewer": "seed"},
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
                    "a": account_id,
                    "c": chart["calculationId"],
                    "cv": chart["calculationVersion"],
                    "rv": chart["rulesVersion"],
                    "pr": f"{chart['provider']['name']}@{chart['provider']['version']}",
                    "r": chart["moon"]["rashi"],
                    "n": chart["moon"]["nakshatra"],
                    "h": chart.get("moonSignHalf"),
                    "ms": chart["mangal"]["status"],
                    "ml": chart["mangal"]["level"],
                    "chart": json.dumps(chart),
                },
            )
            print(f"{name}: {place.label}, rashi {chart['moon']['rashi']}, nakshatra {chart['moon']['nakshatra']}, mangal {chart['mangal']['status']} {chart['mangal']['level'] or ''}")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
