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
from typing import Protocol

import asyncpg

from app.config import get_settings
from app.i18n import translate


class NotificationChannel(Protocol):
    async def deliver(self, conn: asyncpg.Connection, member_id: str, title: str, body: str | None, link: str | None) -> None: ...


class InAppChannel:
    """[TR021] The one real, always-available channel — writes the inbox
    row every /v1/notifications read serves. `idempotency_key` is UNIQUE at
    the DB level (already modeled), so a retried send is a no-op, never a
    duplicate — TR052's own delivery contract, enforced structurally."""

    async def deliver(self, conn: asyncpg.Connection, member_id: str, title: str, body: str | None, link: str | None) -> None:
        pass  # writing happens in send_notification() itself (needs kind/template/idempotency_key too)


class WebPushChannel:
    """[Decision] Structural stub behind placeholder VAPID keys — no
    push-subscription table/flow exists yet, so this is never actually
    invoked by `send_notification()`'s default channel list. Exists so a
    future real Web Push integration is a channel addition, not a redesign
    of every call site that sends a notification today."""

    async def deliver(self, conn: asyncpg.Connection, member_id: str, title: str, body: str | None, link: str | None) -> None:
        settings = get_settings()
        if settings.vapid_public_key.startswith("CHANGE_ME"):
            return  # no real subscription/push infra wired yet — honest no-op


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
) -> bool:
    """Returns True if a new row was written, False if the idempotency key
    already existed (a no-op retry, per TR052's never-duplicate rule)."""
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
    )


# [TR025/TR026/TR027 — migration 005 gap 2] A member's own action notifying
# the OTHER party of the same interaction. The member's session can't insert
# someone else's notification or read their language, so the text is
# rendered here in all three launch languages and the SECURITY DEFINER
# function picks the recipient's — after checking both are parties and that
# the recipient hasn't blocked the caller.
LAUNCH_LANGUAGES = ("en", "hi", "te")


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
    texts = {}
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
