# [TR044] Progressive first-run to Discover (FR44). Five screens, server-
# verified via members.first_run_step/first_run_done — none of them is a
# sign-up/login/OTP-sign-in screen (a structural absence: this file defines
# no credential-related route at all), directly honouring the product
# owner's standing correction that authentication belongs to the parent
# platform alone.
# Approach: GET returns the member's current step so the frontend can
# resume mid-flow after a refresh; POST /step is idempotent per step
# (repeating the same step number just re-saves that step's fields, never
# double-advances). Location-permission-denied falls back to a manual
# `locality` text field on the same call, per TR044's own text.
# Traces to: FR44, TR044, SP044
from __future__ import annotations

from typing import Literal

import asyncpg
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.db import get_conn

router = APIRouter(prefix="/v1/first-run", tags=["first-run"])

TOTAL_STEPS = 5


class FirstRunState(BaseModel):
    step: int
    done: bool
    display_name: str
    language: str
    locality: str | None
    lat: float | None
    lng: float | None
    help_with: list[str]


class FirstRunStepInput(BaseModel):
    step: int
    display_name: str | None = None
    language: Literal["en", "hi", "te"] | None = None
    locality: str | None = None
    lat: float | None = None
    lng: float | None = None
    help_with: list[str] | None = None


@router.get("/state", response_model=FirstRunState)
async def get_first_run_state(conn: asyncpg.Connection = Depends(get_conn)) -> FirstRunState:
    row = await conn.fetchrow(
        """SELECT first_run_step, first_run_done, display_name, language, locality, lat, lng, help_with
           FROM vyapar_identity.members WHERE id = current_setting('vyapar.authz_context', true)"""
    )
    return FirstRunState(
        step=row["first_run_step"],
        done=row["first_run_done"],
        display_name=row["display_name"],
        language=row["language"],
        locality=row["locality"],
        lat=row["lat"],
        lng=row["lng"],
        help_with=list(row["help_with"]),
    )


@router.post("/step", response_model=FirstRunState)
async def save_first_run_step(
    body: FirstRunStepInput, conn: asyncpg.Connection = Depends(get_conn)
) -> FirstRunState:
    # Idempotent: only ever moves first_run_step forward (GREATEST), a
    # repeat POST of an earlier step never regresses progress.
    done = body.step >= TOTAL_STEPS
    row = await conn.fetchrow(
        """UPDATE vyapar_identity.members SET
             first_run_step = GREATEST(first_run_step, $2),
             first_run_done = first_run_done OR $3,
             display_name = COALESCE($4, display_name),
             language = COALESCE($5, language),
             locality = COALESCE($6, locality),
             lat = COALESCE($7, lat),
             lng = COALESCE($8, lng),
             help_with = COALESCE($9, help_with),
             updated_at = now()
           WHERE id = current_setting('vyapar.authz_context', true)
           RETURNING first_run_step, first_run_done, display_name, language, locality, lat, lng, help_with""",
        body.step,
        body.step,
        done,
        body.display_name,
        body.language,
        body.locality,
        body.lat,
        body.lng,
        body.help_with,
    )
    return FirstRunState(
        step=row["first_run_step"],
        done=row["first_run_done"],
        display_name=row["display_name"],
        language=row["language"],
        locality=row["locality"],
        lat=row["lat"],
        lng=row["lng"],
        help_with=list(row["help_with"]),
    )
