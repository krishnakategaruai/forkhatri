# [TR045] Event instrumentation with outcome levels (FR45).
# Approach: one `emit_event()` every server-side action calls directly (most
# of FR45's trigger list — enquiry submitted, review submitted, report
# submitted, notification sent, setup step, promotion purchased/active/
# completed, outcome confirmed — is already a server-side action this app
# processes, so logging it here is more honest than requiring a client round
# trip for something the server already knows happened). `POST /v1/events`
# (batched) exists for the client-observable list the server genuinely
# cannot see on its own — impression, detail view scroll depth, search
# executed, share, notification opened/muted, setup step abandoned.
# `member_pseudo` is never the raw member id: HMAC-SHA256 of the id with a
# server-only secret, truncated to 16 hex chars — stable per member (so the
# same member's events can be grouped) but not reversible without the
# secret, and never the verification-identifier key (a different secret, a
# different threat model). `level` is mandatory and never collapsed. A
# non-`operational` event for a member who has withdrawn behavioral-
# analytics consent is REJECTED here, not merely hidden by a client opt-out a
# modified client could bypass (TR045's own explicit rule) — `operational`
# (state changes) is exempt because a member cannot opt out of Vyapar simply
# functioning.
# Traces to: FR45, TR045, SP045 (implicit — see 08-security-performance.md's
# general Information-disclosure pattern for pseudonymous ids)
from __future__ import annotations

import hashlib
import hmac
import json
from typing import Literal

import asyncpg

from app.config import get_settings

Level = Literal["impression", "view", "action", "attributed_outcome", "confirmed_outcome", "operational"]


def pseudonymize(member_id: str | None) -> str | None:
    if not member_id:
        return None
    secret = get_settings().analytics_pseudonym_secret.encode("utf-8")
    return hmac.new(secret, member_id.encode("utf-8"), hashlib.sha256).hexdigest()[:16]


async def emit_event(
    conn: asyncpg.Connection,
    *,
    member_id: str | None,
    event: str,
    level: Level,
    object_id: str | None = None,
    surface: str | None = None,
    props: dict | None = None,
) -> None:
    if level != "operational" and member_id:
        allowed = await conn.fetchval(
            "SELECT coalesce(behavioral_analytics, true) FROM vyapar_privacy.privacy_settings WHERE member_id = $1", member_id
        )
        if allowed is False:
            return  # [TR045] withdrawn consent — silently skipped, never stored, never bypassable client-side
    await conn.execute(
        "INSERT INTO vyapar_analytics.analytics_events (member_pseudo, object_id, surface, event, level, props) VALUES ($1,$2,$3,$4,$5,$6::jsonb)",
        pseudonymize(member_id), object_id, surface, event, level, json.dumps(props or {}),
    )
