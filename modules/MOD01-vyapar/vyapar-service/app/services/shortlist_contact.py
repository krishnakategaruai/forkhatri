# [Backend A, 2026-09-29 — critique L11, coordinator's product decision]
# "Call shortlisted candidates." WorkIndia and Apna let an employer call the
# people they shortlisted: the candidate consented to being contacted by
# applying. So when a poster moves an applicant to `shortlisted`, the POSTER
# gets the applicant's call / WhatsApp actions, in the same ContactAction
# shape workstream B serves after acceptance (app/services/contact.py).
#
# Rules, all decided here and nowhere else:
#   * one direction only: the poster sees the applicant's number. The
#     applicant sees the poster's number only after hiring/acceptance (B's
#     rule) or through the post's own `allow_precall` switch (B's rule);
#   * the applicant's call hours, daily cap and "matching only" setting do
#     not apply (those protect people from strangers; this person applied).
#     Their channel switches (call_ok / whatsapp_ok) still do: someone who
#     turned calls off entirely is only offered WhatsApp;
#   * only while the stage is `shortlisted` and the thread is not yet
#     accepted (after acceptance B's normal rule takes over). Declining, or
#     moving back to `new`, hides the number again on the very next read;
#   * the number comes only from `contacts_for_viewer(listing, true)`, the
#     one disclosure function, for a listing the applicant owns;
#   * every grant and every hide is written to the audit log by the stage
#     change (applicants.py), and every tap to contact_attempts.
# Traces to: FR22, FR23, FR24, TR024, critique L11
from __future__ import annotations

from typing import Any
from urllib.parse import quote

import asyncpg

from app.i18n import translate
from app.identity import AuthzContext
from app.services.contact import ContactAction, _e164

SHORTLIST_REVEAL_STAGE = "shortlisted"
PRE_ACCEPT_STATES = frozenset({"open", "awaiting_response"})


def shortlist_reveal_applies(enquiry: asyncpg.Record | dict, caller_id: str) -> bool:
    return (
        enquiry["provider_id"] == caller_id
        and enquiry["stage"] == SHORTLIST_REVEAL_STAGE
        and enquiry["state"] in PRE_ACCEPT_STATES
        and enquiry["opportunity_id"] is not None
    )


async def _applicant_listing_id(conn: asyncpg.Connection, enquiry: asyncpg.Record | dict) -> str | None:
    """The applicant's own listing: the one in their snapshot when they still
    own it and it is readable, else their newest active listing."""
    snapshot = enquiry["profile_snapshot"]
    if isinstance(snapshot, str):
        import json

        snapshot = json.loads(snapshot)
    wanted = (snapshot or {}).get("listing_id")
    if wanted:
        try:
            row = await conn.fetchval(
                "SELECT id::text FROM vyapar_listings.listings WHERE id = $1 AND owner_id = $2", wanted, enquiry["sender_id"]
            )
        except asyncpg.DataError:
            row = None
        if row:
            return row
    return await conn.fetchval(
        """SELECT id::text FROM vyapar_listings.listings WHERE owner_id = $1 AND state IN ('active_unverified','active_verified')
           ORDER BY published_at DESC NULLS LAST LIMIT 1""",
        enquiry["sender_id"],
    )


async def shortlist_contact_actions(
    conn: asyncpg.Connection, ctx: AuthzContext, lang: str, enquiry: asyncpg.Record | dict, opportunity_title: str | None = None,
) -> list[dict[str, Any]]:
    """The poster's call / WhatsApp actions for a shortlisted applicant, or []
    when the rule does not apply. Never raises."""
    if not shortlist_reveal_applies(enquiry, ctx.member_id):
        return []
    listing_id = await _applicant_listing_id(conn, enquiry)
    if listing_id is None:
        return []
    contacts = await conn.fetch("SELECT * FROM vyapar_listings.contacts_for_viewer($1, true)", listing_id)
    phone = next((c["value"] for c in contacts if c["channel"] == "phone"), None)
    whatsapp = next((c["value"] for c in contacts if c["channel"] == "whatsapp"), None) or phone
    phone = phone or whatsapp
    prefs = await conn.fetchrow("SELECT call_ok, whatsapp_ok FROM vyapar_identity.contact_preferences_for($1)", enquiry["sender_id"])
    call_ok = True if prefs is None or prefs["call_ok"] is None else bool(prefs["call_ok"])
    whatsapp_ok = True if prefs is None or prefs["whatsapp_ok"] is None else bool(prefs["whatsapp_ok"])

    names = {r["id"]: r["display_name"] for r in await conn.fetch(
        "SELECT id, display_name FROM vyapar_identity.public_names($1::text[])", [enquiry["sender_id"], ctx.member_id])}
    if opportunity_title is None:
        opportunity_title = await conn.fetchval(
            "SELECT title FROM vyapar_opportunities.opportunities WHERE id = $1", enquiry["opportunity_id"]) or ""

    actions: list[dict[str, Any]] = []
    e164 = _e164(phone or "")
    if call_ok and e164:
        actions.append(ContactAction(
            channel="call", label=translate("contact.channel.call", lang), href=f"tel:{e164}", available_now=True,
        ).model_dump())
    wa = _e164(whatsapp or "")
    if whatsapp_ok and wa:
        text = translate("contact.prefill.whatsapp", lang, name=names.get(enquiry["sender_id"], ""), subject=opportunity_title,
                         me=names.get(ctx.member_id) or "")
        actions.append(ContactAction(
            channel="whatsapp", label=translate("contact.channel.whatsapp", lang),
            href=f"https://wa.me/{wa.lstrip('+')}?text={quote(text)}", available_now=True,
        ).model_dump())
    return actions
