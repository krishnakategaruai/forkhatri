# [Recommendations that learn, 2026-09-30] Loading, refreshing, showing and
# controlling a member's learned taste. The model itself is app/taste.py
# (pure); this file is the only place that reads or writes
# vyapar_privacy.member_taste.
#
# Refresh: the taste is rebuilt from the member's own actions whenever they
# change. `load_taste()` reads the actions through the self-or-dispatcher
# definer functions of migration 030 (content columns only), fingerprints
# them, and rebuilds only when the fingerprint moved or the stored model is
# more than an hour old (time decay). So every action — save, apply, hide,
# "More like this", a hire — shows up on the very next read, with no hook in
# each write path, and an unsave or an un-hide is honoured the same way.
# The hourly loop (`run_taste_refresh_pass`) keeps stored models current for
# the alert passes.
#
# Control (FR36/FR37/FR38): GET shows what was learned in the member's
# language; DELETE resets (actions before the reset never count again); PATCH
# removes one item (actions before the removal no longer count for it);
# "More like this" is a strong positive. When the member turns off
# personalised recommendations or usage analytics, nothing is learned or
# used: the stored model is emptied and the reset point moves to "now", so
# actions taken while it was off are not learned later either.
# Traces to: FR19, FR20, FR36, FR37, FR38, FR55, TR019, TR020, SP019
from __future__ import annotations

import hashlib
import json
import logging
import math
from datetime import datetime, timedelta, timezone
from typing import Literal

import asyncpg
from pydantic import BaseModel, Field

from app.errors import ApiError
from app.i18n import translate
from app.identity import AuthzContext
from app.taste import (
    Taste, PostEvents, build_model, word_label, listing_features, monthly_top, post_features, project_top, WINDOW_DAYS,
)
from app.taxonomy_cache import label_for

logger = logging.getLogger(__name__)

STALE_AFTER = timedelta(hours=1)
_OPP_ACTIONS = ("saved_at", "viewed_at", "hidden_at", "shared_at", "external_opened_at", "completed_at",
                "more_like_this_at", "applied_at", "hired_at", "withdrawn_at")
_LISTING_ACTIONS = ("saved_at", "viewed_at", "contacted_at")
SPECIAL_ITEMS = ("distance_limit", "pay_floor")
_KIND_OF = {"skill": "skill", "cat": "category", "type": "post_type", "mode": "work_mode", "shift": "shift",
            "pay": "pay", "dist": "distance", "exp": "experience", "word": "word",
            "lskill": "profile_skill", "lcat": "profile_category", "lkind": "profile_kind", "ldist": "profile_distance"}


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class TasteItemOut(BaseModel):
    id: str = Field(description="Stable item id, e.g. skill:electrical, type:employment, dist:3_8, distance_limit, pay_floor")
    kind: str = Field(description="skill | category | post_type | work_mode | shift | pay | distance | experience | word | "
                                  "profile_skill | profile_category | profile_kind | profile_distance | distance_limit | pay_floor")
    label: str = Field(description="What it is, in the member's language")
    direction: Literal["like", "avoid"]
    source: Literal["applied", "saved", "other"] | None = Field(default=None, description="The kind of action it was mostly learned from")
    strength: float = Field(description="0..1 relative to the strongest item of its kind")


class TasteOut(BaseModel):
    enabled: bool = Field(description="False when the member turned off personalised recommendations or usage analytics")
    confidence: float = Field(description="0 with no history, 1 after 10 meaningful actions; how much taste counts in ranking")
    actions_counted: int
    summary: list[str] = Field(description="Human-readable lines in the member's language")
    summary_text: str = Field(description="The same lines joined with ' · '")
    likes: list[TasteItemOut]
    avoids: list[TasteItemOut]
    distance_limit_km: float | None = Field(default=None, description="Learned from 'Too far'; never below 3 km")
    pay_floor_paise: int | None = Field(default=None, description="Monthly pay floor learned from 'Pay too low'")
    usual_distance_km: float | None = None
    usual_monthly_pay_paise: int | None = None
    updated_at: datetime | None = None


class TastePatch(BaseModel):
    remove: str = Field(min_length=3, max_length=120, description="The id of one item from likes or avoids")


# ---------------------------------------------------------------------------
# Loading and refreshing
# ---------------------------------------------------------------------------
def _haversine(lat1, lng1, lat2, lng2) -> float | None:
    if None in (lat1, lng1, lat2, lng2):
        return None
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _parse_removed(raw) -> dict[str, datetime]:
    if isinstance(raw, str):
        raw = json.loads(raw or "{}")
    out = {}
    for k, v in (raw or {}).items():
        try:
            out[k] = datetime.fromisoformat(v)
        except (TypeError, ValueError):
            continue
    return out


def _model(raw) -> dict:
    if isinstance(raw, str):
        return json.loads(raw or "{}")
    return dict(raw or {})


async def _allowed(conn: asyncpg.Connection, member_id: str) -> bool:
    return bool(await conn.fetchval("SELECT vyapar_privacy.personalisation_allowed($1)", member_id))


async def _events(conn: asyncpg.Connection, member_id: str) -> tuple[list[PostEvents], str]:
    member = await conn.fetchrow("SELECT lat, lng FROM vyapar_identity.members WHERE id = $1", member_id)
    lat, lng = (member["lat"], member["lng"]) if member else (None, None)
    since = datetime.now(timezone.utc) - timedelta(days=WINDOW_DAYS)
    opp_rows = await conn.fetch("SELECT * FROM vyapar_opportunities.member_taste_events($1, $2)", member_id, since)
    lst_rows = await conn.fetch("SELECT * FROM vyapar_listings.member_taste_listing_events($1, $2)", member_id, since)
    h = hashlib.sha1(f"{lat},{lng}".encode())
    events: list[PostEvents] = []
    for r in opp_rows:
        h.update(repr([str(r["opportunity_id"])] + [r[a] for a in _OPP_ACTIONS] + [r["hidden_reason"]]).encode())
        d = _haversine(lat, lng, r["lat"], r["lng"])
        actions = {a[:-3]: r[a] for a in _OPP_ACTIONS if r[a] is not None}
        # a hidden post counts as hidden; the rest of its actions are overridden in build_model
        events.append(PostEvents(features=post_features(r, d), actions=actions, hidden_reason=r["hidden_reason"],
                                 distance_km=d, monthly=monthly_top(r), project=project_top(r)))
    for r in lst_rows:
        h.update(repr([str(r["listing_id"])] + [r[a] for a in _LISTING_ACTIONS]).encode())
        d = _haversine(lat, lng, r["lat"], r["lng"])
        actions = {a[:-3]: r[a] for a in _LISTING_ACTIONS if r[a] is not None}
        events.append(PostEvents(features=listing_features(r, d), actions=actions, distance_km=d, listing=True))
    return events, h.hexdigest()


async def load_taste(conn: asyncpg.Connection, member_id: str, *, force: bool = False) -> Taste:
    """The member's current taste, rebuilt when their actions changed. Runs as
    the member (or the dispatcher); never as an operator reading someone else."""
    if not member_id:
        return Taste.empty()
    try:
        allowed = await _allowed(conn, member_id)
    except asyncpg.PostgresError:
        logger.exception("taste: personalisation check failed")
        return Taste.empty()
    row = await conn.fetchrow("SELECT * FROM vyapar_privacy.member_taste WHERE member_id = $1", member_id)
    if not allowed:
        if row is not None and (_model(row["model"]) or row["fingerprint"]):
            await conn.execute(
                "UPDATE vyapar_privacy.member_taste SET model = '{}', fingerprint = NULL, reset_at = now(), updated_at = now() WHERE member_id = $1",
                member_id)
        elif row is None:
            await conn.execute(
                "INSERT INTO vyapar_privacy.member_taste (member_id, reset_at) VALUES ($1, now()) ON CONFLICT (member_id) DO UPDATE SET reset_at = now()",
                member_id)
        else:
            await conn.execute("UPDATE vyapar_privacy.member_taste SET reset_at = now() WHERE member_id = $1", member_id)
        return Taste.empty(enabled=False)
    events, fp = await _events(conn, member_id)
    reset_at = row["reset_at"] if row else None
    removed = _parse_removed(row["removed"]) if row else {}
    fp = hashlib.sha1(f"{fp}|{reset_at}|{sorted((k, v.isoformat()) for k, v in removed.items())}".encode()).hexdigest()
    now = datetime.now(timezone.utc)
    if row is not None and not force and row["fingerprint"] == fp and row["updated_at"] > now - STALE_AFTER:
        return Taste(_model(row["model"]))
    if row is None and not events:
        return Taste.empty()  # nothing to learn, nothing stored
    model = build_model(events, now=now, reset_at=reset_at, removed=removed)
    await conn.execute(
        """INSERT INTO vyapar_privacy.member_taste (member_id, model, fingerprint, updated_at) VALUES ($1, $2::jsonb, $3, now())
           ON CONFLICT (member_id) DO UPDATE SET model = EXCLUDED.model, fingerprint = EXCLUDED.fingerprint, updated_at = now()""",
        member_id, json.dumps(model), fp,
    )
    return Taste(model)


async def taste_or_empty(conn: asyncpg.Connection, member_id: str) -> Taste:
    """For ranking reads: a taste problem must never break a feed."""
    try:
        async with conn.transaction():  # a savepoint: a failure here leaves the request's transaction usable
            return await load_taste(conn, member_id)
    except Exception:
        logger.exception("taste: load failed for %s", member_id)
        return Taste.empty()


# ---------------------------------------------------------------------------
# Showing it
# ---------------------------------------------------------------------------
def _label(key: str, lang: str) -> str:
    group, value = key.split(":", 1)
    if group in ("skill", "cat", "lskill", "lcat"):
        return label_for(value, lang)
    if group in ("type", "mode", "shift", "pay", "dist", "exp", "lkind", "ldist"):
        g = {"lkind": "profileKind", "ldist": "dist"}.get(group, group)
        return translate(f"ranking.taste.{g}.{value}", lang)
    return word_label(value)


def _format_inr(paise: int) -> str:
    from app.services.opportunities import format_inr

    return format_inr(paise)


def taste_out(taste: Taste, lang: str, updated_at: datetime | None = None) -> TasteOut:
    m = taste.model if taste.enabled else {}
    w = m.get("w") or {}
    src = m.get("src") or {}
    max_abs: dict[str, float] = {}
    for k, v in w.items():
        g = k.split(":", 1)[0]
        max_abs[g] = max(max_abs.get(g, 0.0), abs(v))
    likes, avoids = [], []
    for k, v in sorted(w.items(), key=lambda kv: (-abs(kv[1]), kv[0])):
        g = k.split(":", 1)[0]
        strength = abs(v) / max_abs[g] if max_abs.get(g) else 0.0
        if strength < 0.15 or g not in _KIND_OF:
            continue
        item = TasteItemOut(id=k, kind=_KIND_OF[g], label=_label(k, lang), direction="like" if v > 0 else "avoid",
                            source=src.get(k) if v > 0 else None, strength=round(strength, 2))
        (likes if v > 0 else avoids).append(item)
    likes = likes[:15]
    dist_limit = m.get("dist_limit")
    pay_floor = (m.get("pay_floor") or {}).get("monthly")
    if dist_limit:
        avoids.append(TasteItemOut(id="distance_limit", kind="distance_limit", direction="avoid", strength=1.0,
                                   label=translate("ranking.taste.item.distanceLimit", lang, km=_km(dist_limit))))
    if pay_floor:
        avoids.append(TasteItemOut(id="pay_floor", kind="pay_floor", direction="avoid", strength=1.0,
                                   label=translate("ranking.taste.item.payFloor", lang, amount=_format_inr(pay_floor))))

    usual = m.get("usual") or {}
    summary: list[str] = []
    applied = taste.top("skill", "applied") or taste.top("cat", "applied")
    if applied:
        summary.append(translate("ranking.taste.summary.applied", lang, items=", ".join(label_for(s, lang) for s in applied)))
    saved = [s for s in taste.top("skill", "saved") if s not in applied]
    if saved:
        summary.append(translate("ranking.taste.summary.saved", lang, items=", ".join(label_for(s, lang) for s in saved)))
    km = min(x for x in (dist_limit, usual.get("km")) if x) if (dist_limit or usual.get("km")) else None
    if km:
        summary.append(translate("ranking.taste.summary.within", lang, km=_km(km)))
    pay = max(x for x in (pay_floor, usual.get("monthly")) if x) if (pay_floor or usual.get("monthly")) else None
    if pay:
        summary.append(translate("ranking.taste.summary.pay", lang, amount=_format_inr(pay)))
    avoid = list(m.get("avoid") or [])
    if avoid:
        summary.append(translate("ranking.taste.summary.avoid", lang, items=", ".join(label_for(s, lang) for s in avoid)))
    if not taste.enabled:
        summary = [translate("ranking.taste.summary.off", lang)]
    elif not summary:
        summary = [translate("ranking.taste.summary.nothingYet", lang)]
    return TasteOut(
        enabled=taste.enabled, confidence=round(taste.confidence, 2), actions_counted=int(m.get("n") or 0) + int(m.get("ln") or 0),
        summary=summary, summary_text=" · ".join(summary), likes=likes, avoids=avoids,
        distance_limit_km=dist_limit, pay_floor_paise=pay_floor, usual_distance_km=usual.get("km"),
        usual_monthly_pay_paise=usual.get("monthly"), updated_at=updated_at,
    )


def _km(km: float) -> int:
    return int(math.ceil(km))


async def _updated_at(conn: asyncpg.Connection, member_id: str) -> datetime | None:
    return await conn.fetchval("SELECT updated_at FROM vyapar_privacy.member_taste WHERE member_id = $1", member_id)


async def get_my_taste(conn: asyncpg.Connection, ctx: AuthzContext, lang: str) -> TasteOut:
    taste = await load_taste(conn, ctx.member_id)
    return taste_out(taste, lang, await _updated_at(conn, ctx.member_id))


async def reset_my_taste(conn: asyncpg.Connection, ctx: AuthzContext, lang: str) -> TasteOut:
    """Forget everything learned. Actions before now never count again."""
    await conn.execute(
        """INSERT INTO vyapar_privacy.member_taste (member_id, model, fingerprint, reset_at, removed, updated_at)
           VALUES ($1, '{}', NULL, now(), '{}', now())
           ON CONFLICT (member_id) DO UPDATE SET model = '{}', fingerprint = NULL, reset_at = now(), removed = '{}', updated_at = now()""",
        ctx.member_id,
    )
    return await get_my_taste(conn, ctx, lang)


async def remove_taste_item(conn: asyncpg.Connection, ctx: AuthzContext, lang: str, body: TastePatch) -> TasteOut:
    """Stop using one learned item (a skill, a kind of post, the distance limit ...)."""
    current = taste_out(await load_taste(conn, ctx.member_id), lang)
    known = {i.id for i in current.likes + current.avoids} | set((await _stored_model(conn, ctx.member_id)).get("w") or {})
    if body.remove not in known:
        raise ApiError(404, "ranking.error.tasteItemNotFound", lang)
    # A removed skill also lifts its "not my skill" filter (same id); removing
    # distance_limit / pay_floor drops the "Too far" / "Pay too low" learning.
    await conn.execute(
        """INSERT INTO vyapar_privacy.member_taste (member_id, removed) VALUES ($1, jsonb_build_object($2::text, to_jsonb(now())))
           ON CONFLICT (member_id) DO UPDATE
              SET removed = member_taste.removed || jsonb_build_object($2::text, to_jsonb(now())), fingerprint = NULL, updated_at = now()""",
        ctx.member_id, body.remove,
    )
    taste = await load_taste(conn, ctx.member_id, force=True)
    return taste_out(taste, lang, await _updated_at(conn, ctx.member_id))


async def _stored_model(conn: asyncpg.Connection, member_id: str) -> dict:
    raw = await conn.fetchval("SELECT model FROM vyapar_privacy.member_taste WHERE member_id = $1", member_id)
    return _model(raw)


async def more_like_this(conn: asyncpg.Connection, ctx: AuthzContext, lang: str, opportunity_id: str) -> TasteOut:
    """A strong positive the member gives on purpose."""
    try:
        row = await conn.fetchrow("SELECT id, poster_id FROM vyapar_opportunities.opportunities WHERE id = $1", opportunity_id)
    except asyncpg.DataError:
        row = None
    if row is None:
        raise ApiError(404, "common.error.opportunityNotFound", lang)
    if row["poster_id"] == ctx.member_id:
        raise ApiError(400, "ranking.error.ownPost", lang)
    await conn.execute(
        """INSERT INTO vyapar_opportunities.member_opportunity (member_id, opportunity_id, more_like_this_at) VALUES ($1, $2, now())
           ON CONFLICT (member_id, opportunity_id) DO UPDATE SET more_like_this_at = now(), hidden_at = NULL, hidden_reason = NULL""",
        ctx.member_id, opportunity_id,
    )
    taste = await load_taste(conn, ctx.member_id, force=True)
    return taste_out(taste, lang, await _updated_at(conn, ctx.member_id))


# ---------------------------------------------------------------------------
# Privacy: export, deletion, switch
# ---------------------------------------------------------------------------
async def export_taste(conn: asyncpg.Connection, member_id: str, lang: str) -> dict:
    row = await conn.fetchrow("SELECT * FROM vyapar_privacy.member_taste WHERE member_id = $1", member_id)
    if row is None:
        return {"stored": False}
    taste = Taste(_model(row["model"]))
    return {
        "stored": True,
        "shown": taste_out(taste, lang, row["updated_at"]).model_dump(mode="json"),
        "model": _model(row["model"]),
        "reset_at": row["reset_at"].isoformat() if row["reset_at"] else None,
        "removed": _model(row["removed"]),
        "updated_at": row["updated_at"].isoformat(),
    }


async def delete_taste(conn: asyncpg.Connection, member_id: str) -> None:
    await conn.execute("DELETE FROM vyapar_privacy.member_taste WHERE member_id = $1", member_id)


async def forget_on_switch_off(conn: asyncpg.Connection, member_id: str) -> None:
    """Personalisation (or usage analytics) was turned off: empty the model
    now, and never learn from what happened while it is off."""
    await conn.execute(
        """INSERT INTO vyapar_privacy.member_taste (member_id, model, fingerprint, reset_at, updated_at)
           VALUES ($1, '{}', NULL, now(), now())
           ON CONFLICT (member_id) DO UPDATE SET model = '{}', fingerprint = NULL, reset_at = now(), updated_at = now()""",
        member_id,
    )


# ---------------------------------------------------------------------------
# Hourly refresh (decay, and actions since the last read)
# ---------------------------------------------------------------------------
async def run_taste_refresh_pass(pool) -> dict:
    refreshed = 0
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute("SELECT set_config('vyapar.service_role', 'dispatcher', true)")
            await conn.execute("SELECT set_config('vyapar.authz_context', 'm_neha_ops', true)")
            ids = [r["member_id"] for r in await conn.fetch(
                """SELECT member_id FROM vyapar_privacy.member_taste
                   UNION
                   SELECT DISTINCT member_id FROM vyapar_opportunities.member_opportunity
                    WHERE greatest(saved_at, hidden_at, shared_at, more_like_this_at, external_opened_at) > now() - interval '2 hours'
                   UNION
                   SELECT DISTINCT sender_id FROM vyapar_enquiries.enquiries WHERE updated_at > now() - interval '2 hours'""")]
            for member_id in ids:
                try:
                    async with conn.transaction():
                        await load_taste(conn, member_id)
                    refreshed += 1
                except Exception:
                    logger.exception("taste refresh failed for %s", member_id)
    return {"refreshed": refreshed}
