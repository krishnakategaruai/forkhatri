"""Horoscope — Mangalya's side of kundli matching.

The calculation lives in `modules/MOD03-mangaly/horoscope-service`: planet
positions from a pinned, validated library; Guna Milan scored with Mangalya's
own koota tables, checked against Drik Panchang and AstroSage; Mangal Dosha
with the placements that cause it. This module:

  * builds the person's birth details from their profile (date of birth,
    `horoscope.birth_time` + `birth_time_accuracy`, and the place chosen from
    the list, `horoscope.birth_place_geo`, which carries its time zone);
  * asks the service for the chart and stores it, append-only, in
    `mangaly_horoscope.chart` (migration 056);
  * for a pair, reads both current charts (who may read them is decided in
    SQL: exactly who may read the biodata), asks the service for the match,
    stores it, and returns it.

Nothing here invents data: no birth time means precision UNKNOWN, and the
service reports only what holds for the whole day; no chosen place means no
chart, because without a time zone the time cannot be placed.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal
from uuid import UUID

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.components.profile import interface as profile
from app.components.profile.horoscope_fields import ACCURACY_MINUTES
from app.components.profile.models import FieldState
from app.config.settings import get_settings

logger = logging.getLogger(__name__)

__all__ = ["HoroscopeFilterUnavailable", "HoroscopeUnavailable", "MatchOutcome", "filter_ids", "match_for", "refresh_chart"]


class HoroscopeUnavailable(Exception):
    """The calculation service could not be reached or refused the request."""


class HoroscopeFilterUnavailable(Exception):
    """The person searched for has no chart, so a horoscope filter cannot apply."""


Missing = Literal["NO_PROFILE", "NO_BIRTH_PLACE", "NO_CHART_SELF", "NO_CHART_OTHER", "SAME_GENDER"]


@dataclass(slots=True)
class MatchOutcome:
    """Either a match result from the service, or the reason there is none."""

    result: dict[str, Any] | None
    missing: Missing | None = None


async def _call(path: str, body: dict[str, Any]) -> dict[str, Any]:
    settings = get_settings()
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(
                f"{settings.horoscope_service_url}{path}",
                json=body,
                headers={
                    "authorization": f"Bearer {settings.horoscope_service_token}",
                    "x-mangaly-viewer": "mangaly-service",
                },
            )
    except httpx.HTTPError as exc:
        raise HoroscopeUnavailable("horoscope service unreachable") from exc
    if res.status_code != 200:
        # The service's error names fields, never values; log the code only.
        code = (res.json().get("error") or {}).get("code") if res.headers.get("content-type", "").startswith("application/json") else None
        logger.warning("horoscope service refused %s: %s %s", path, res.status_code, code)
        raise HoroscopeUnavailable(code or f"status {res.status_code}")
    return res.json()


def _birth_details(dob: str, attrs: dict[str, tuple[FieldState, Any]]) -> dict[str, Any] | None:
    def value(key: str) -> Any:
        state, v = attrs.get(key, (None, None))
        return v if state == FieldState.VALUE else None

    geo = value("birth_place_geo")
    if not isinstance(geo, dict) or "timezone" not in geo:
        return None
    accuracy = value("birth_time_accuracy")
    time = value("birth_time")
    details: dict[str, Any] = {
        "birthDate": dob,
        "birthLocation": str(geo.get("label") or geo.get("name") or "place"),
        "latitude": float(geo["latitude"]),
        "longitude": float(geo["longitude"]),
        "timezone": str(geo["timezone"]),
    }
    minutes = ACCURACY_MINUTES.get(accuracy) if isinstance(accuracy, str) else 0
    if not time or accuracy == "unknown":
        details.update(birthTime=None, birthTimePrecision="UNKNOWN")
    elif not minutes:
        # "exact", or a time given without saying how sure: taken as stated.
        details.update(birthTime=time, birthTimePrecision="EXACT")
    else:
        details.update(birthTime=time, birthTimePrecision="APPROXIMATE", birthTimeUncertaintyMinutes=minutes)
    return details


async def refresh_chart(session: AsyncSession, *, account_id: UUID) -> Missing | None:
    """Recalculate and store the caller's own chart from their profile. Returns
    why no chart could be made, or None when the current chart is stored."""
    own = await profile.get_own_profile(session, account_id=account_id)
    if own is None:
        return "NO_PROFILE"
    attrs = await profile.get_category(session, account_id=account_id, category="horoscope") or {}
    details = _birth_details(own.date_of_birth.isoformat(), attrs)
    if details is None:
        return "NO_BIRTH_PLACE"
    chart = await _call("/horoscope/calculate/chart", {"birthDetails": details})
    moon = chart.get("moon") or {}
    await session.execute(
        text(
            """
            INSERT INTO mangaly_horoscope.chart
                (account_id, calculation_id, calculation_version, rules_version, provider,
                 rashi, nakshatra, moon_sign_half, mangal_status, mangal_level, chart)
            VALUES (:account, :calc, :cver, :rules, :provider, :rashi, :nak, :half, :mangal, :level, CAST(:chart AS jsonb))
            ON CONFLICT (account_id, calculation_id) DO NOTHING
            """
        ),
        {
            "account": account_id,
            "calc": chart["calculationId"],
            "cver": chart["calculationVersion"],
            "rules": chart["rulesVersion"],
            "provider": f"{chart['provider']['name']}@{chart['provider']['version']}",
            "rashi": moon.get("rashi"),
            "nak": moon.get("nakshatra"),
            "half": chart.get("moonSignHalf"),
            "mangal": (chart.get("mangal") or {}).get("status"),
            "level": (chart.get("mangal") or {}).get("level"),
            "chart": json.dumps(chart),
        },
    )
    return None


async def _current_with_gender(session: AsyncSession, account_id: UUID) -> tuple[dict[str, Any], str] | None:
    """The person's newest chart and their gender, if the caller may read them
    (decided in SQL: the same people who may read the biodata)."""
    row = (
        await session.execute(
            text("SELECT chart, gender FROM mangaly_horoscope.current_chart(:a)"), {"a": account_id}
        )
    ).first()
    return (row[0], row[1]) if row else None


async def _current(session: AsyncSession, account_id: UUID) -> dict[str, Any] | None:
    found = await _current_with_gender(session, account_id)
    return found[0] if found else None


async def match_for(
    session: AsyncSession, *, candidate_account_id: UUID, other_account_id: UUID
) -> MatchOutcome:
    """Guna Milan and Mangal Dosha between a candidate (the viewer, or the
    person a family member is acting for) and another person."""
    own = await _current_with_gender(session, candidate_account_id)
    if own is None:
        return MatchOutcome(None, "NO_CHART_SELF")
    other = await _current_with_gender(session, other_account_id)
    if other is None:
        return MatchOutcome(None, "NO_CHART_OTHER")
    (mine, g_self), (theirs, g_other) = own, other
    if g_self == g_other:
        return MatchOutcome(None, "SAME_GENDER")
    # Ashtakoota is asymmetric: the groom's chart goes first.
    groom, bride = (mine, theirs) if g_self == "male" else (theirs, mine)
    groom_id, bride_id = (
        (candidate_account_id, other_account_id) if g_self == "male" else (other_account_id, candidate_account_id)
    )
    result = await _call("/horoscope/calculate/match", {"groom": groom, "bride": bride})
    await session.execute(
        text(
            "SELECT mangaly_horoscope.save_match(:id, :g, :b, :gc, :bc, :rules, :total, CAST(:porutham AS smallint), CAST(:result AS jsonb))"
        ),
        {
            "id": result["matchId"],
            "g": groom_id,
            "b": bride_id,
            "gc": groom["calculationId"],
            "bc": bride["calculationId"],
            "rules": result["rulesVersion"],
            "total": (result.get("ashtakoota") or {}).get("totalScore"),
            "porutham": (result.get("porutham") or {}).get("agreed"),
            "result": json.dumps(result),
        },
    )
    return MatchOutcome(result)


async def _placements_and_scores(
    session: AsyncSession,
    *,
    seeker_account_id: UUID,
    seeker_gender: str,
    candidate_ids: list[UUID],
    keep: Callable[[dict[str, Any]], bool] | None = None,
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    """Moon placements of `candidate_ids` (those with a chart, and passing
    `keep`) paired with their Ashtakoota/Porutham scores against the seeker,
    in batches of 500. Raises HoroscopeFilterUnavailable when the seeker has
    no chart."""
    mine = await _current(session, seeker_account_id)
    if mine is None or mine.get("rashi") is None or mine.get("nakshatra") is None:
        raise HoroscopeFilterUnavailable
    rows = (
        await session.execute(
            text("SELECT * FROM mangaly_horoscope.placements(CAST(:ids AS uuid[]))"),
            {"ids": [str(i) for i in candidate_ids]},
        )
    ).mappings().all()
    seeker_moon = {"rashi": mine["rashi"], "nakshatra": mine["nakshatra"], "signHalf": mine.get("moonSignHalf")}
    kept = [
        dict(r)
        for r in rows
        if r["rashi"] is not None and r["nakshatra"] is not None and (keep is None or keep({**r, "seeker": mine}))
    ]
    out: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for start in range(0, len(kept), 500):
        batch = kept[start : start + 500]
        pairs = []
        for r in batch:
            other = {"rashi": r["rashi"], "nakshatra": r["nakshatra"], "signHalf": r["moon_sign_half"]}
            groom, bride = (seeker_moon, other) if seeker_gender == "male" else (other, seeker_moon)
            pairs.append({"groom": groom, "bride": bride})
        scores = (await _call("/horoscope/calculate/scores", {"pairs": pairs}))["scores"]
        out.extend(zip(batch, scores, strict=True))
    return out


async def guna_scores(
    session: AsyncSession,
    *,
    seeker_account_id: UUID,
    seeker_gender: str,
    candidate_ids: list[UUID],
) -> dict[UUID, float]:
    """[Owner, 2026-09-28] Guna Milan (out of 36) between the seeker and each
    of `candidate_ids` who has a chart — Discover's "Matched by horoscope"
    row. Empty when the seeker has no chart."""
    if not candidate_ids:
        return {}
    try:
        scored = await _placements_and_scores(
            session, seeker_account_id=seeker_account_id, seeker_gender=seeker_gender, candidate_ids=candidate_ids
        )
    except HoroscopeFilterUnavailable:
        return {}
    return {
        r["account_id"]: float(sc["totalScore"])
        for r, sc in scored
        if sc.get("status") == "CALCULATED" and sc.get("totalScore") is not None
    }


async def filter_ids(
    session: AsyncSession,
    *,
    seeker_account_id: UUID,
    seeker_gender: str,
    candidate_ids: list[UUID],
    min_guna: float | None,
    mangal: str | None,
    min_porutham: int | None = None,
    porutham_essentials: bool = False,
) -> set[UUID]:
    """[Owner, 2026-09-27] Discover's optional horoscope filter, switched on by
    the member: who among `candidate_ids` has a Guna Milan of at least
    `min_guna` with the seeker, and (mangal = "match") the same Mangal Dosha
    presence as the seeker, or (mangal = "none") no Mangal Dosha. People
    without a chart cannot be scored and are not returned. Raises
    HoroscopeFilterUnavailable when the seeker has no chart."""

    def mangal_ok(r: dict[str, Any]) -> bool:
        seeker_mangal = (r["seeker"].get("mangal") or {}).get("status")
        if mangal == "none" and r["mangal_status"] != "ABSENT":
            return False
        if mangal == "match":
            if seeker_mangal not in ("PRESENT", "ABSENT") or r["mangal_status"] not in ("PRESENT", "ABSENT"):
                return False
            if (seeker_mangal == "PRESENT") != (r["mangal_status"] == "PRESENT"):
                return False
        return True

    if min_guna is None and min_porutham is None and not porutham_essentials:
        # Mangal only: no scores needed, the placements decide.
        mine = await _current(session, seeker_account_id)
        if mine is None or mine.get("rashi") is None or mine.get("nakshatra") is None:
            raise HoroscopeFilterUnavailable
        rows = (
            await session.execute(
                text("SELECT * FROM mangaly_horoscope.placements(CAST(:ids AS uuid[]))"),
                {"ids": [str(i) for i in candidate_ids]},
            )
        ).mappings().all()
        return {
            r["account_id"]
            for r in rows
            if r["rashi"] is not None and r["nakshatra"] is not None and mangal_ok({**r, "seeker": mine})
        }

    result: set[UUID] = set()
    for r, sc in await _placements_and_scores(
        session,
        seeker_account_id=seeker_account_id,
        seeker_gender=seeker_gender,
        candidate_ids=candidate_ids,
        keep=mangal_ok,
    ):
        if min_guna is not None and not (sc.get("status") == "CALCULATED" and sc.get("totalScore") is not None and sc["totalScore"] >= min_guna):
            continue
        if min_porutham is not None and not (sc.get("poruthamAgreed") is not None and sc["poruthamAgreed"] >= min_porutham):
            continue
        if porutham_essentials and sc.get("essentialsAgree") is not True:
            continue
        result.add(r["account_id"])
    return result
