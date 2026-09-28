"""Horoscope routes — the Guna Milan and Mangal Dosha between the candidate
in context and another person, calculated by the horoscope service.

A traditional, optional layer: the result is shown as it is (score out of
36, each koota, where Mars sits), never as a verdict, and it never changes
who is shown, in what order, or whether a request can be sent — except
through the Discover filter a member switches on themselves.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.api.deps import AuthenticatedAccount, DbSession
from app.components.authorization import interface as authz
from app.components.authorization.context import AuthorizationDenied
from app.components.horoscope import interface as horoscope

router = APIRouter(prefix="/horoscope", tags=["horoscope"])


class MatchResponse(BaseModel):
    # One of: the match result, or why there is none (NO_CHART_SELF, NO_CHART_OTHER, SAME_GENDER, NO_BIRTH_PLACE).
    available: bool
    missing: str | None = None
    match: dict[str, Any] | None = None
    # Which traditional matching the candidate's family follows: "ashtakoota",
    # "porutham" or "both" — their own choice, else by mother tongue.
    preferred_system: str = "both"


_SOUTH_INDIAN = {"telugu", "tamil", "kannada", "malayalam"}


async def _preferred_system(session: DbSession, candidate: UUID, viewer: UUID) -> str:
    """The candidate's chosen matching style; if unset, Porutham for families
    whose mother tongue is a South Indian language, Guna Milan otherwise."""
    from app.components.profile import interface as profile

    if candidate == viewer:
        horoscope_attrs = await profile.get_category(session, account_id=viewer, category="horoscope") or {}
        basics = await profile.get_category(session, account_id=viewer, category="basics") or {}
        chosen = horoscope_attrs.get("matching_system", (None, None))
        tongue = basics.get("mother_tongue", (None, None))
        chosen_value = chosen[1] if str(chosen[0]) == "value" else None
        tongue_value = tongue[1] if str(tongue[0]) == "value" else None
    else:
        biodata = await profile.public_biodata(session, account_id=candidate)
        chosen_value = (biodata.get("horoscope") or {}).get("matching_system")
        tongue_value = (biodata.get("basics") or {}).get("mother_tongue")
    if chosen_value in ("ashtakoota", "porutham", "both"):
        return str(chosen_value)
    return "porutham" if str(tongue_value or "").lower() in _SOUTH_INDIAN else "ashtakoota"


@router.get("/match/{other_account_id}", response_model=MatchResponse)
async def get_match(
    other_account_id: UUID,
    session: DbSession,
    account_id: AuthenticatedAccount,
    for_candidate: UUID | None = None,
) -> MatchResponse:
    try:
        candidate = await authz.resolve_context_account(
            session, acting_account_id=account_id, for_candidate=for_candidate
        )
    except AuthorizationDenied as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN) from exc

    try:
        outcome = await horoscope.match_for(session, candidate_account_id=candidate, other_account_id=other_account_id)
        # The candidate's own chart may simply not be calculated yet (details
        # saved before this feature, or a rules update): they may make it now.
        if outcome.missing == "NO_CHART_SELF" and candidate == account_id:
            missing = await horoscope.refresh_chart(session, account_id=account_id)
            if missing:
                return MatchResponse(available=False, missing=missing)
            outcome = await horoscope.match_for(session, candidate_account_id=candidate, other_account_id=other_account_id)
    except horoscope.HoroscopeUnavailable as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="horoscope_unavailable") from exc

    preferred = await _preferred_system(session, candidate, account_id)
    if outcome.result is None:
        return MatchResponse(available=False, missing=outcome.missing, preferred_system=preferred)
    return MatchResponse(available=True, match=outcome.result, preferred_system=preferred)


# ---------------------------------------------------------------------------
# Kundli matching page: any two people's birth details, calculated and shown,
# never stored. Traditional matching only — no predictions.
# ---------------------------------------------------------------------------


class CheckPerson(BaseModel):
    birth_date: str
    birth_time: str | None = None
    # exact | about_15 | about_30 | about_60 | about_120 | unknown
    accuracy: str = "exact"
    place_id: str


class CheckRequest(BaseModel):
    groom: CheckPerson
    bride: CheckPerson


@router.post("/check", response_model=MatchResponse)
async def check(body: CheckRequest, account_id: AuthenticatedAccount) -> MatchResponse:
    """Guna Milan, Porutham and Mangal Dosha for two people entered by hand
    (a proposal from outside Mangaly, relatives…). Signed-in members only;
    nothing entered here is stored or logged."""
    import re
    from datetime import date

    from app.components.places import interface as places
    from app.components.profile.horoscope_fields import ACCURACY

    charts = []
    for side, person in (("groom", body.groom), ("bride", body.bride)):
        try:
            date.fromisoformat(person.birth_date)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail={"code": "invalid_value", "key": f"{side}.birth_date"}) from exc
        if person.accuracy not in ACCURACY:
            raise HTTPException(status_code=422, detail={"code": "invalid_value", "key": f"{side}.accuracy"})
        if person.accuracy != "unknown" and not (person.birth_time and re.match(r"^([01]\d|2[0-3]):[0-5]\d$", person.birth_time)):
            raise HTTPException(status_code=422, detail={"code": "invalid_value", "key": f"{side}.birth_time"})
        place = places.get(person.place_id)
        if place is None:
            raise HTTPException(status_code=422, detail={"code": "invalid_value", "key": f"{side}.place"})
        details: dict[str, Any] = {
            "birthDate": person.birth_date,
            "birthLocation": place.label,
            "latitude": place.latitude,
            "longitude": place.longitude,
            "timezone": place.timezone,
        }
        minutes = {"exact": 0, "about_15": 15, "about_30": 30, "about_60": 60, "about_120": 120}.get(person.accuracy)
        if person.accuracy == "unknown":
            details.update(birthTime=None, birthTimePrecision="UNKNOWN")
        elif not minutes:
            details.update(birthTime=person.birth_time, birthTimePrecision="EXACT")
        else:
            details.update(birthTime=person.birth_time, birthTimePrecision="APPROXIMATE", birthTimeUncertaintyMinutes=minutes)
        try:
            charts.append(await horoscope._call("/horoscope/calculate/chart", {"birthDetails": details}))
        except horoscope.HoroscopeUnavailable as exc:
            # The service refuses impossible input (e.g. a time skipped by a clock change) by code, never by value.
            raise HTTPException(status_code=422, detail={"code": "invalid_value", "key": side, "reason": str(exc)}) from exc
    try:
        match = await horoscope._call("/horoscope/calculate/match", {"groom": charts[0], "bride": charts[1]})
    except horoscope.HoroscopeUnavailable as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="horoscope_unavailable") from exc
    return MatchResponse(available=True, match=match, preferred_system="both")
