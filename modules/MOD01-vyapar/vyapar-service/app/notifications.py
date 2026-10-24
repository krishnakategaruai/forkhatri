# [TR021] Notification Bridge: one real delivery channel today (in-app
# inbox), a second behind the same interface for later (Web Push) — the
# product owner's explicit instruction: "build it genuinely rather than
# waiting for a platform Notification Service... later the platform
# Notification Service becomes an adapter swap, not a rewrite."
# Approach: `NotificationChannel` is the swap seam (mirrors `PaymentGateway`'s
# own already-established pattern in this codebase, per TR051/CCR13) — every
# caller sends through `send_notification()`, never writes to the
# `notifications` table directly. `InAppChannel` is real: it writes the
# already-modeled `vyapar_integration.notifications` row, which IS the
# always-available inbox UX18 names. `WebPushChannel` is a structural stub
# behind placeholder VAPID keys (config-placeholder convention) — never
# invoked by default, since no push-subscription flow exists yet in this
# session; wiring a real subscription flow is future work, not silently
# faked here.
# Traces to: FR21, TR021, TR052 (idempotent, never-duplicate delivery contract)
from __future__ import annotations

import json

import asyncpg

from app.i18n import translate


# [IMP37] The channel adapters moved to app/integrations/notifications/;
# re-exported here so existing imports keep working.
from app.integrations.notifications.channels import InAppChannel, NotificationChannel, WebPushChannel  # noqa: E402,F401


async def send_notification(
    conn: asyncpg.Connection,
    *,
    member_id: str,
    kind: str,
    template_id: str,
    title: str,
    body: str | None,
    link: str | None,
    params: dict,
    idempotency_key: str,
    i18n: dict | None = None,
) -> bool:
    """Returns True if a new row was written, False if the idempotency key
    already existed (a no-op retry, per TR052's never-duplicate rule).

    [IMP-B, owner 2026-09-30] `i18n` is the template the text came from —
    {"title": key, "body": key, "values": {...}, "key_values": {name: key}} —
    stored under params._i18n so the inbox renders it in the READER's
    language at read time (render_notification); `title`/`body` stay as the
    write-time rendering, used only when a template can't be resolved."""
    if i18n:
        params = {**params, "_i18n": i18n}
    row = await conn.fetchrow(
        """INSERT INTO vyapar_integration.notifications
             (member_id, kind, template_id, title, body, link, params, idempotency_key)
           VALUES ($1,$2,$3,$4,$5,$6,$7::jsonb,$8)
           ON CONFLICT (idempotency_key) DO NOTHING
           RETURNING id""",
        member_id, kind, template_id, title, body, link, json.dumps(params), idempotency_key,
    )
    return row is not None


async def notify_member(
    conn: asyncpg.Connection,
    *,
    member_id: str,
    template: str,
    link: str,
    idempotency_key: str,
    params: dict[str, str] | None = None,
    key_params: dict[str, str] | None = None,
) -> bool:
    """[TR030/TR031/TR051] A notification rendered in the recipient's own
    language. The caller must be able to read that member's language row —
    the member themself, or a system/operator context (webhook, scheduled
    job, operator action)."""
    lang = await conn.fetchval("SELECT language FROM vyapar_identity.members WHERE id = $1", member_id) or "en"
    values = dict(params or {})
    for name, key in (key_params or {}).items():
        values[name] = translate(key, lang)
    return await send_notification(
        conn, member_id=member_id, kind=template, template_id=template,
        title=translate(f"notifications.{template}.title", lang, **values),
        body=translate(f"notifications.{template}.body", lang, **values),
        link=link, params=values, idempotency_key=idempotency_key,
        i18n={"title": f"notifications.{template}.title", "body": f"notifications.{template}.body",
              "values": dict(params or {}), "key_values": dict(key_params or {})},
    )


# [TR025/TR026/TR027 — migration 005 gap 2] A member's own action notifying
# the OTHER party of the same interaction. The member's session can't insert
# someone else's notification or read their language, so the text is
# rendered here in all three launch languages and the SECURITY DEFINER
# function picks the recipient's — after checking both are parties and that
# the recipient hasn't blocked the caller.
LAUNCH_LANGUAGES = ("en", "hi", "te", "mr", "kn")


async def notify_interaction_party(
    conn: asyncpg.Connection,
    *,
    interaction_kind: str,
    interaction_id,
    recipient: str,
    template: str,
    link: str,
    idempotency_key: str,
    params: dict[str, str] | None = None,
    key_params: dict[str, str] | None = None,
) -> bool:
    """`params` are literal values (e.g. a listing name); `key_params` map a
    placeholder to an i18n key translated per language (e.g. a state word)."""
    texts: dict = {"_i18n": {"title": f"notifications.{template}.title", "body": f"notifications.{template}.body",
                             "values": dict(params or {}), "key_values": dict(key_params or {})}}
    for lang in LAUNCH_LANGUAGES:
        values = dict(params or {})
        for name, key in (key_params or {}).items():
            values[name] = translate(key, lang)
        texts[lang] = {
            "title": translate(f"notifications.{template}.title", lang, **values),
            "body": translate(f"notifications.{template}.body", lang, **values),
        }
    return await conn.fetchval(
        "SELECT vyapar_integration.notify_interaction_party($1, $2, $3, $4, $5::jsonb, $6, $7)",
        interaction_kind, interaction_id, recipient, template, json.dumps(texts, ensure_ascii=False), link, idempotency_key,
    )



# ---------------------------------------------------------------------------
# [IMP-B, owner 2026-09-30: notifications "are rendered in English for
# everyone"] Read-time rendering in the reader's language. Three sources, in
# order: the stored template spec (params._i18n, or inside params._texts when
# a SQL function stored the caller's texts), the per-language texts a SQL
# function kept (params._texts), then the stored text. A template whose
# placeholder can't be filled, or whose key is missing, falls back rather
# than showing "{name}" or a raw key.
# ---------------------------------------------------------------------------
def _render_spec(spec: dict, lang: str) -> tuple[str | None, str | None]:
    values = {k: v for k, v in (spec.get("values") or {}).items()}
    for name, key in (spec.get("key_values") or {}).items():
        values[name] = translate(key, lang)
    out = []
    for part in ("title", "body"):
        key = spec.get(part)
        if not key:
            out.append(None)
            continue
        text = translate(key, lang, **values)
        out.append(None if text == key or ("{" in text and "}" in text) else text)
    return out[0], out[1]


def render_notification(row, lang: str) -> tuple[str, str | None]:
    params = row["params"]
    if isinstance(params, str):
        params = json.loads(params)
    params = params or {}
    texts = params.get("_texts") if isinstance(params.get("_texts"), dict) else {}
    spec = params.get("_i18n") or texts.get("_i18n")
    if isinstance(spec, dict):
        title, body = _render_spec(spec, lang)
        if title:
            return title, body if body is not None else row["body"]
    picked = texts.get(lang) or texts.get("en")
    if isinstance(picked, dict) and picked.get("title"):
        return picked["title"], picked.get("body")
    return row["title"], row["body"]
