"""Booking lifecycle — one explicit state machine.

pending_payment -> confirmed -> in_progress -> completed
                 \\-> expired          \\-> cancelled_by_* / no_show_*
Refunds follow the cancellation policy snapshotted on the booking. Payouts
become eligible `payout_hold_hours` after completion."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

import asyncpg

from app.components import audit, money, notifications
from app.errors import DomainError, forbidden, not_found

LIVE = ("pending_payment", "confirmed", "in_progress")
PENDING_TTL = timedelta(minutes=15)


async def get(conn, booking_id: UUID) -> dict:
    b = await conn.fetchrow("SELECT * FROM booking WHERE id=$1", booking_id)
    if not b:
        raise not_found("booking")
    return dict(b)


def participant(b: dict, member_id: UUID) -> str:
    if b["seeker_id"] == member_id:
        return "seeker"
    if b["provider_id"] == member_id:
        return "provider"
    raise forbidden("This booking is not yours.")


async def create(conn, *, seeker_id: UUID, service: dict, starts_at: datetime, brief: str, seeker_tz: str, purchase: dict | None = None) -> dict:
    if service["provider_id"] == seeker_id:
        raise DomainError("own_service", "You cannot book your own service.")
    q = await money.quote(conn, service["price_minor"], service["currency"])
    if purchase:
        from app.components.purchases import session_share
        share = session_share(purchase)
        q = money.Quote(share["gross_minor"], share["platform_fee_minor"], 0, 0, share["provider_payable_minor"], purchase["currency"], q.platform_fee_percent)
    policy = await money.cancellation_policy(conn)
    ends_at = starts_at + timedelta(minutes=service["duration_min"])
    try:
        row = await conn.fetchrow(
            """
            INSERT INTO booking (service_id, provider_id, seeker_id, starts_at, ends_at, seeker_timezone, brief,
                                 service_title, duration_min, currency, gross_minor, platform_fee_minor, processing_fee_minor,
                                 tax_minor, provider_payable_minor, cancellation_policy, recording_allowed, formats, purchase_id)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18,$19) RETURNING *
            """,
            service["id"], service["provider_id"], seeker_id, starts_at, ends_at, seeker_tz, brief,
            service["title"], service["duration_min"], q.currency, q.gross_minor, q.platform_fee_minor,
            q.processing_fee_minor, q.tax_minor, q.provider_payable_minor, policy, service["recording_allowed"], service["formats"],
            purchase["id"] if purchase else None,
        )
    except asyncpg.ExclusionViolationError:
        raise DomainError("slot_taken", "That time was just taken. Pick another slot.", 409) from None
    b = dict(row)
    if purchase:
        # Paid for with the package: confirmed now, no second payment.
        await conn.execute("UPDATE booking SET status='confirmed', updated_at=now() WHERE id=$1", b["id"])
        await money.ledger(conn, b["id"], "provider_payable", q.provider_payable_minor, q.currency, f"package {purchase['id']}")
        await _on_confirmed(conn, await get(conn, b["id"]))
        await audit.record(conn, seeker_id, "booking.created", "booking", b["id"], {"starts_at": starts_at.isoformat(), "package": str(purchase["id"])})
        return await get(conn, b["id"])
    pay = money.provider()
    intent = await pay.create_payment(b["id"], q.gross_minor, q.currency)
    await conn.execute(
        "INSERT INTO payment (booking_id, provider_name, external_ref, amount_minor, currency, status) VALUES ($1,$2,$3,$4,$5,'created')",
        b["id"], pay.name, intent.external_ref, q.gross_minor, q.currency,
    )
    b["checkout"] = {"external_ref": intent.external_ref, **intent.checkout}
    await audit.record(conn, seeker_id, "booking.created", "booking", b["id"], {"starts_at": starts_at.isoformat()})
    return b


async def confirm_payment(conn, *, booking_id: UUID, actor_id: UUID, proof: dict) -> dict:
    b = await get(conn, booking_id)
    if b["seeker_id"] != actor_id:
        raise forbidden()
    if b["status"] != "pending_payment":
        return b
    p = await conn.fetchrow("SELECT * FROM payment WHERE booking_id=$1 ORDER BY created_at DESC LIMIT 1", booking_id)
    if b["pay_by"] and b["pay_by"] < datetime.now(timezone.utc):
        raise DomainError("hold_expired", "The held time has lapsed. Propose another time.", 409)
    ok = await money.provider().verify_payment(p["external_ref"], proof)
    if not ok:
        await conn.execute("UPDATE payment SET status='failed', updated_at=now() WHERE id=$1", p["id"])
        raise DomainError("payment_failed", "The payment did not go through.", 402)
    await conn.execute("UPDATE payment SET status='succeeded', updated_at=now() WHERE id=$1", p["id"])
    await conn.execute("UPDATE booking SET status='confirmed', updated_at=now() WHERE id=$1", booking_id)
    cur = b["currency"]
    await money.ledger(conn, booking_id, "gross", b["gross_minor"], cur)
    await money.ledger(conn, booking_id, "platform_fee", -b["platform_fee_minor"], cur)
    if b["processing_fee_minor"]:
        await money.ledger(conn, booking_id, "processing_fee", -b["processing_fee_minor"], cur)
    if b["tax_minor"]:
        await money.ledger(conn, booking_id, "tax", -b["tax_minor"], cur)
    await money.ledger(conn, booking_id, "provider_payable", b["provider_payable_minor"], cur)
    await _on_confirmed(conn, b)
    await audit.record(conn, actor_id, "payment.succeeded", "booking", booking_id, {"amount_minor": b["gross_minor"]})
    return await get(conn, booking_id)


async def _on_confirmed(conn, b: dict) -> None:
    booking_id = b["id"]
    await conn.execute("INSERT INTO note (booking_id, owner_id, body) VALUES ($1, NULL, '') ON CONFLICT DO NOTHING", booking_id)
    await conn.execute("INSERT INTO message (booking_id, sender_id, kind, body) VALUES ($1, NULL, 'system', 'booking_confirmed')", booking_id)
    await notifications.notify(conn, b["provider_id"], "booking.new", {"title": b["service_title"], "starts_at": b["starts_at"].isoformat()}, booking_id)
    await notifications.notify(conn, b["seeker_id"], "booking.confirmed", {"title": b["service_title"], "starts_at": b["starts_at"].isoformat()}, booking_id)


async def _refund(conn, b: dict, percent: int, note: str) -> int:
    amount = round(b["gross_minor"] * percent / 100)
    if amount <= 0:
        return 0
    p = await conn.fetchrow("SELECT * FROM payment WHERE booking_id=$1 AND status IN ('succeeded','partially_refunded') ORDER BY created_at DESC LIMIT 1", b["id"])
    if not p:
        return 0
    await money.provider().refund(p["external_ref"], amount)
    new_total = p["refunded_minor"] + amount
    await conn.execute("UPDATE payment SET refunded_minor=$2, status=$3, updated_at=now() WHERE id=$1",
                       p["id"], new_total, "refunded" if new_total >= p["amount_minor"] else "partially_refunded")
    await money.ledger(conn, b["id"], "refund", -amount, b["currency"], note)
    # The provider's payable shrinks with the refund; the platform fee is returned proportionally.
    await conn.execute("UPDATE booking SET refund_minor = refund_minor + $2 WHERE id=$1", b["id"], amount)
    return amount


async def cancel(conn, *, booking_id: UUID, actor_id: UUID, reason: str) -> dict:
    b = await get(conn, booking_id)
    role = participant(b, actor_id)
    if b["status"] not in ("pending_payment", "confirmed"):
        raise DomainError("not_cancellable", "This booking can no longer be cancelled.", 409)
    policy = b["cancellation_policy"]
    if b["status"] == "pending_payment":
        percent = 0
        new_status = "expired"
    elif role == "seeker":
        percent = money.refund_percent_for_seeker_cancel(policy, b["starts_at"])
        new_status = "cancelled_by_seeker"
    else:
        percent = int(policy.get("provider_cancel_refund_percent", 100))
        new_status = "cancelled_by_provider"
    refunded = 0
    if b["purchase_id"] and b["status"] == "confirmed":
        # A package session: a full-refund cancellation gives the session back.
        if percent >= 100:
            from app.components.purchases import return_session
            await return_session(conn, b["purchase_id"])
    elif b["status"] == "confirmed":
        refunded = await _refund(conn, b, percent, f"{new_status}: {reason}")
    await conn.execute(
        "UPDATE booking SET status=$2, cancel_reason=$3, cancelled_by=$4, cancelled_at=now(), updated_at=now() WHERE id=$1",
        booking_id, new_status, reason, actor_id,
    )
    await conn.execute("INSERT INTO message (booking_id, sender_id, kind, body) VALUES ($1, NULL, 'system', $2)", booking_id, new_status)
    other = b["provider_id"] if role == "seeker" else b["seeker_id"]
    if reason == "member_deleted":
        # The other person is told plainly that the member left, never who they were.
        await notifications.notify(conn, other, "booking.cancelled_deleted", {"title": b["service_title"], "refund_minor": refunded}, booking_id)
    else:
        await notifications.notify(conn, other, "booking.cancelled", {"title": b["service_title"], "by": role, "refund_minor": refunded}, booking_id)
    await audit.record(conn, actor_id, "booking.cancelled", "booking", booking_id, {"role": role, "refund_percent": percent, "refunded_minor": refunded, "reason": reason})
    return await get(conn, booking_id)


async def start(conn, booking_id: UUID) -> None:
    await conn.execute("UPDATE booking SET status='in_progress', updated_at=now() WHERE id=$1 AND status='confirmed'", booking_id)


async def complete(conn, *, booking_id: UUID, actor_id: UUID) -> dict:
    b = await get(conn, booking_id)
    participant(b, actor_id)
    if b["status"] not in ("confirmed", "in_progress"):
        raise DomainError("not_completable", "This booking cannot be marked complete.", 409)
    await conn.execute("UPDATE booking SET status='completed', completed_at=now(), payout_status='eligible', updated_at=now() WHERE id=$1", booking_id)
    await conn.execute("INSERT INTO message (booking_id, sender_id, kind, body) VALUES ($1, NULL, 'system', 'completed')", booking_id)
    await notifications.notify(conn, b["seeker_id"], "review.available", {"title": b["service_title"]}, booking_id)
    await notifications.notify(conn, b["provider_id"], "payout.eligible", {"amount_minor": b["provider_payable_minor"] - b["refund_minor"]}, booking_id)
    await audit.record(conn, actor_id, "booking.completed", "booking", booking_id)
    await build_recap(conn, booking_id)
    from app.components import badges
    await badges.refresh(conn, b["provider_id"])
    return await get(conn, booking_id)


async def no_show(conn, *, booking_id: UUID, actor_id: UUID) -> dict:
    """The present party reports the other did not turn up (only after the start time)."""
    b = await get(conn, booking_id)
    role = participant(b, actor_id)
    if b["status"] not in ("confirmed", "in_progress"):
        raise DomainError("not_applicable", "No-show can only be recorded for a confirmed booking.", 409)
    if datetime.now(timezone.utc) < b["starts_at"] + timedelta(minutes=10):
        raise DomainError("too_early", "Wait at least 10 minutes after the start time.", 409)
    policy = b["cancellation_policy"]
    if role == "provider":
        new_status, percent = "no_show_seeker", int(policy.get("seeker_no_show_refund_percent", 0))
        payout = "eligible"
    else:
        new_status, percent = "no_show_provider", int(policy.get("provider_no_show_refund_percent", 100))
        payout = "none"
    refunded = 0
    if b["purchase_id"]:
        if percent >= 100:
            from app.components.purchases import return_session
            await return_session(conn, b["purchase_id"])
    else:
        refunded = await _refund(conn, b, percent, new_status)
    await conn.execute("UPDATE booking SET status=$2, payout_status=$3, updated_at=now() WHERE id=$1", booking_id, new_status, payout)
    await conn.execute("INSERT INTO message (booking_id, sender_id, kind, body) VALUES ($1, NULL, 'system', $2)", booking_id, new_status)
    other = b["provider_id"] if role == "seeker" else b["seeker_id"]
    await notifications.notify(conn, other, "booking.no_show", {"title": b["service_title"], "status": new_status, "refund_minor": refunded}, booking_id)
    await audit.record(conn, actor_id, "booking.no_show", "booking", booking_id, {"status": new_status, "refunded_minor": refunded})
    return await get(conn, booking_id)


async def expire_stale(conn) -> int:
    """Pending bookings whose checkout was abandoned release the slot."""
    res = await conn.execute(
        "UPDATE booking SET status='expired', updated_at=now() WHERE status='pending_payment' "
        "AND ((pay_by IS NULL AND created_at < $1) OR pay_by < now() OR starts_at < now())", datetime.now(timezone.utc) - PENDING_TTL)
    return int(res.split()[-1])


async def auto_progress(conn) -> None:
    """Confirmed bookings whose time has come become in_progress; bookings well past
    their end with nobody acting are completed (both parties can still dispute)."""
    now = datetime.now(timezone.utc)
    await conn.execute("UPDATE booking SET status='in_progress', updated_at=now() WHERE status='confirmed' AND starts_at <= $1", now)
    stale = await conn.fetch("SELECT id FROM booking WHERE status='in_progress' AND ends_at < $1", now - timedelta(hours=24))
    for r in stale:
        await conn.execute("UPDATE booking SET status='completed', completed_at=now(), payout_status='eligible', updated_at=now() WHERE id=$1", r["id"])
        await conn.execute("INSERT INTO message (booking_id, sender_id, kind, body) VALUES ($1, NULL, 'system', 'completed')", r["id"])


async def build_recap(conn, booking_id: UUID) -> str:
    """After-call recap (GrowthMentor-style, but private): the shared notes, the
    action items and the files, in one message both people keep. When AI is
    switched on, a short summary of the shared notes is added on top."""
    b = await get(conn, booking_id)
    note = (await conn.fetchval("SELECT body FROM note WHERE booking_id=$1 AND owner_id IS NULL", booking_id) or "").strip()
    actions = await conn.fetch("SELECT text, done FROM action_item WHERE booking_id=$1 ORDER BY created_at", booking_id)
    files = await conn.fetch("SELECT name FROM file WHERE booking_id=$1 AND deleted_at IS NULL ORDER BY created_at", booking_id)
    parts: list[str] = []
    from app.components import ai
    summary = await ai.summarise(note) if note else None
    if summary:
        parts.append("## Summary\n" + summary)
    if note:
        parts.append("## Notes\n" + note)
    if actions:
        parts.append("## Action items\n" + "\n".join(f"- [{'x' if a['done'] else ' '}] {a['text']}" for a in actions))
    if files:
        parts.append("## Files\n" + "\n".join(f"- {f['name']}" for f in files))
    recap = "\n\n".join(parts)
    if not recap:
        return ""
    await conn.execute("UPDATE booking SET recap=$2, recap_at=now() WHERE id=$1", booking_id, recap)
    await conn.execute("INSERT INTO message (booking_id, sender_id, kind, body) VALUES ($1, NULL, 'system', 'recap_ready')", booking_id)
    for m in (b["seeker_id"], b["provider_id"]):
        await notifications.notify(conn, m, "booking.recap", {"title": b["service_title"]}, booking_id)
    return recap


async def send_reminders(conn) -> int:
    """Two reminders per confirmed booking: the day before and 15 minutes before
    (when the room opens). Each is sent once; the timestamps make it idempotent."""
    sent = 0
    now = datetime.now(timezone.utc)
    for col, window, kind in (("reminded_24h_at", timedelta(hours=24), "booking.reminder_day"), ("reminded_15m_at", timedelta(minutes=15), "booking.reminder_now")):
        rows = await conn.fetch(
            f"SELECT id, seeker_id, provider_id, service_title, starts_at FROM booking WHERE status='confirmed' AND {col} IS NULL AND starts_at > $1 AND starts_at <= $2",
            now, now + window)
        for r in rows:
            for m in (r["seeker_id"], r["provider_id"]):
                await notifications.notify(conn, m, kind, {"title": r["service_title"], "starts_at": r["starts_at"].isoformat()}, r["id"])
            await conn.execute(f"UPDATE booking SET {col}=now() WHERE id=$1", r["id"])
            sent += 1
    return sent


async def request_payout(conn, provider_id: UUID) -> dict:
    if not await conn.fetchval("SELECT 1 FROM payout_method WHERE provider_id=$1", provider_id):
        raise DomainError("payout_method_required", "Add where you want to be paid first.", 409)
    hold = int(await money.setting(conn, "payout_hold_hours", 24))
    rows = await conn.fetch(
        "SELECT id, provider_payable_minor - refund_minor AS amt, currency FROM booking WHERE provider_id=$1 AND payout_status='eligible' AND completed_at < $2",
        provider_id, datetime.now(timezone.utc) - timedelta(hours=hold))
    questions = await conn.fetch(
        "SELECT id, provider_payable_minor AS amt, currency FROM purchase WHERE provider_id=$1 AND kind='question' AND payout_status='eligible' AND updated_at < $2",
        provider_id, datetime.now(timezone.utc) - timedelta(hours=hold))
    total = sum(max(r["amt"], 0) for r in rows) + sum(r["amt"] for r in questions)
    if total <= 0:
        raise DomainError("nothing_to_pay", "Nothing is ready for payout yet.", 409)
    cur = (rows[0] if rows else questions[0])["currency"]
    ref = await money.provider().create_payout(provider_id, total, cur)
    payout_id = await conn.fetchval(
        "INSERT INTO payout (provider_id, amount_minor, currency, status, external_ref, paid_at) VALUES ($1,$2,$3,'paid',$4,now()) RETURNING id",
        provider_id, total, cur, ref)
    for r in rows:
        await conn.execute("UPDATE booking SET payout_status='paid', payout_id=$2 WHERE id=$1", r["id"], payout_id)
        await money.ledger(conn, r["id"], "payout", -max(r["amt"], 0), cur, str(payout_id))
    for r in questions:
        await conn.execute("UPDATE purchase SET payout_status='paid' WHERE id=$1", r["id"])
        await conn.execute("INSERT INTO ledger_entry (purchase_id, kind, amount_minor, currency, note) VALUES ($1,'payout',$2,$3,$4)", r["id"], -r["amt"], cur, str(payout_id))
    await audit.record(conn, provider_id, "payout.paid", "payout", payout_id, {"amount_minor": total})
    return {"id": str(payout_id), "amount_minor": total, "currency": cur}
