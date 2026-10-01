"""Follow-ups and paid questions: money that is not tied to one booking.

Follow-ups ("package" in the data): 1–3 check-ins with the same consultant on the
same problem, bought only after a completed consultation, used within `valid_days`.
  * Bought and paid once (a purchase). Each session booked from it is confirmed
    immediately and carries its per-session share of the price, fee and payable,
    so payouts stay per completed session.
  * Unused sessions are refunded automatically when the package expires, or
    when the buyer cancels the package (pro-rata to unused sessions).
Question: a written question at the consultant's question price.
  * Answered in writing within `question_answer_days`, or refunded in full
    automatically. The consultant is paid once they answer.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from app.components import audit, money, notifications
from app.errors import DomainError, forbidden, not_found


async def _ledger(conn, purchase_id: UUID, kind: str, amount: int, currency: str, note: str | None = None) -> None:
    await conn.execute("INSERT INTO ledger_entry (purchase_id, kind, amount_minor, currency, note) VALUES ($1,$2,$3,$4,$5)",
                       purchase_id, kind, amount, currency, note)


async def _create(conn, *, kind: str, buyer_id: UUID, service: dict, price_minor: int, package: dict | None = None) -> dict:
    if service["provider_id"] == buyer_id:
        raise DomainError("own_service", "You cannot buy your own service.")
    q = await money.quote(conn, price_minor, service["currency"])
    pay = money.provider()
    row = await conn.fetchrow(
        """INSERT INTO purchase (kind, buyer_id, provider_id, package_id, service_id, sessions_total, currency, gross_minor, platform_fee_minor, provider_payable_minor)
           VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10) RETURNING *""",
        kind, buyer_id, service["provider_id"], package["id"] if package else None, service["id"], package["sessions"] if package else None,
        q.currency, q.gross_minor, q.platform_fee_minor, q.provider_payable_minor)
    intent = await pay.create_payment(row["id"], q.gross_minor, q.currency)
    await conn.execute("UPDATE purchase SET external_ref=$2 WHERE id=$1", row["id"], intent.external_ref)
    return {**dict(row), "external_ref": intent.external_ref, "checkout": intent.checkout}


async def _mark_paid(conn, p: dict, proof: dict) -> None:
    if not await money.provider().verify_payment(p["external_ref"], proof):
        raise DomainError("payment_failed", "The payment did not go through.", 402)
    cur = p["currency"]
    await _ledger(conn, p["id"], "gross", p["gross_minor"], cur)
    await _ledger(conn, p["id"], "platform_fee", -p["platform_fee_minor"], cur)


# --- Packages ---------------------------------------------------------------------------

async def buy_package(conn, *, buyer_id: UUID, package_id: UUID) -> dict:
    pk = await conn.fetchrow("SELECT * FROM package WHERE id=$1 AND active", package_id)
    if not pk:
        raise not_found("package")
    svc = await conn.fetchrow("SELECT * FROM service WHERE id=$1 AND status='active'", pk["service_id"])
    if not svc:
        raise not_found("service")
    # Follow-ups continue advice already given: only after a completed consultation with this consultant.
    if not await conn.fetchval("SELECT 1 FROM booking WHERE seeker_id=$1 AND provider_id=$2 AND status='completed'", buyer_id, svc["provider_id"]):
        raise DomainError("follow_up_needs_first", "Follow-ups are offered after a first consultation with this consultant.", 409)
    return await _create(conn, kind="package", buyer_id=buyer_id, service=dict(svc), price_minor=pk["price_minor"], package=dict(pk))


async def pay(conn, *, purchase_id: UUID, actor_id: UUID, proof: dict) -> dict:
    p = await conn.fetchrow("SELECT * FROM purchase WHERE id=$1", purchase_id)
    if not p or p["buyer_id"] != actor_id:
        raise not_found("purchase")
    p = dict(p)
    if p["status"] != "pending_payment":
        return p
    await _mark_paid(conn, p, proof)
    if p["kind"] == "package":
        days = await conn.fetchval("SELECT valid_days FROM package WHERE id=$1", p["package_id"])
        await conn.execute("UPDATE purchase SET status='active', expires_at=$2, updated_at=now() WHERE id=$1", purchase_id, datetime.now(timezone.utc) + timedelta(days=days))
        title = await conn.fetchval("SELECT title FROM service WHERE id=$1", p["service_id"])
        await notifications.notify(conn, p["provider_id"], "package.bought", {"title": title, "sessions": p["sessions_total"]})
    else:
        await conn.execute("UPDATE purchase SET status='active', updated_at=now() WHERE id=$1", purchase_id)
        q = await conn.fetchrow("SELECT q.due_at, s.title FROM question q JOIN service s ON s.id=q.service_id WHERE q.purchase_id=$1", purchase_id)
        await notifications.notify(conn, p["provider_id"], "question.new", {"title": q["title"], "due": q["due_at"].isoformat()})
    await audit.record(conn, actor_id, f"{p['kind']}.paid", "purchase", purchase_id, {"amount_minor": p["gross_minor"]})
    return dict(await conn.fetchrow("SELECT * FROM purchase WHERE id=$1", purchase_id))


def session_share(p: dict) -> dict:
    n = p["sessions_total"]
    return {"gross_minor": p["gross_minor"] // n, "platform_fee_minor": p["platform_fee_minor"] // n, "provider_payable_minor": p["provider_payable_minor"] // n}


async def use_session(conn, purchase_id: UUID, buyer_id: UUID, service_id: UUID) -> dict:
    p = await conn.fetchrow("SELECT * FROM purchase WHERE id=$1 FOR UPDATE", purchase_id)
    if not p or p["buyer_id"] != buyer_id or p["kind"] != "package":
        raise not_found("package")
    if p["service_id"] != service_id:
        raise DomainError("wrong_service", "This package is for another consultation.", 422)
    if p["status"] != "active" or (p["expires_at"] and p["expires_at"] < datetime.now(timezone.utc)):
        raise DomainError("package_inactive", "This package is not active.", 409)
    if p["sessions_used"] >= p["sessions_total"]:
        raise DomainError("package_used_up", "All sessions in this package are used.", 409)
    used = p["sessions_used"] + 1
    await conn.execute("UPDATE purchase SET sessions_used=$2, status=$3, updated_at=now() WHERE id=$1", purchase_id, used,
                       "used_up" if used >= p["sessions_total"] else "active")
    return dict(p)


async def return_session(conn, purchase_id: UUID) -> None:
    await conn.execute("UPDATE purchase SET sessions_used=greatest(sessions_used-1,0), status=CASE WHEN status='used_up' THEN 'active' ELSE status END, updated_at=now() WHERE id=$1",
                       purchase_id)


async def refund_unused(conn, purchase_id: UUID, reason: str, actor_id: UUID | None = None) -> int:
    p = dict(await conn.fetchrow("SELECT * FROM purchase WHERE id=$1 FOR UPDATE", purchase_id))
    booked = await conn.fetchval("SELECT count(*) FROM booking WHERE purchase_id=$1 AND status IN ('confirmed','in_progress')", purchase_id)
    if booked:
        raise DomainError("sessions_booked", "Cancel the booked sessions first.", 409)
    unused = p["sessions_total"] - p["sessions_used"]
    amount = session_share(p)["gross_minor"] * unused
    if amount > 0:
        await money.provider().refund(p["external_ref"], amount)
        await _ledger(conn, purchase_id, "refund", -amount, p["currency"], reason)
    await conn.execute("UPDATE purchase SET refund_minor=refund_minor+$2, status=$3, updated_at=now() WHERE id=$1", purchase_id, amount,
                       "refunded" if p["sessions_used"] == 0 else "expired" if reason == "expired" else "cancelled")
    await notifications.notify(conn, p["buyer_id"], "package.refunded", {"refund_minor": amount, "sessions": unused})
    await audit.record(conn, actor_id, "package.refunded", "purchase", purchase_id, {"amount_minor": amount, "unused": unused, "reason": reason})
    return amount


# --- Questions ---------------------------------------------------------------------------

async def ask(conn, *, buyer_id: UUID, service_id: UUID, body: str) -> dict:
    svc = await conn.fetchrow("SELECT * FROM service WHERE id=$1 AND status='active'", service_id)
    if not svc:
        raise not_found("service")
    if not svc["question_price_minor"]:
        raise DomainError("questions_off", "This consultant does not take written questions.", 409)
    if await conn.fetchval("SELECT 1 FROM block WHERE (member_id=$1 AND blocked_id=$2) OR (member_id=$2 AND blocked_id=$1)", buyer_id, svc["provider_id"]):
        raise forbidden("This consultant is not available to you.")
    open_count = await conn.fetchval("SELECT count(*) FROM purchase WHERE buyer_id=$1 AND provider_id=$2 AND kind='question' AND status IN ('pending_payment','active')",
                                     buyer_id, svc["provider_id"])
    if open_count >= 2:
        raise DomainError("too_many_requests", "You already have questions waiting with this consultant.", 429)
    p = await _create(conn, kind="question", buyer_id=buyer_id, service=dict(svc), price_minor=svc["question_price_minor"])
    await conn.execute("INSERT INTO question (purchase_id, service_id, body, due_at) VALUES ($1,$2,$3,$4)",
                       p["id"], service_id, body, datetime.now(timezone.utc) + timedelta(days=svc["question_answer_days"]))
    return p


async def answer(conn, *, purchase_id: UUID, provider_id: UUID, text: str) -> None:
    p = await conn.fetchrow("SELECT * FROM purchase WHERE id=$1 FOR UPDATE", purchase_id)
    if not p or p["provider_id"] != provider_id or p["kind"] != "question":
        raise not_found("question")
    if p["status"] != "active":
        raise DomainError("not_open", "This question is no longer open.", 409)
    await conn.execute("UPDATE question SET answer=$2, answered_at=now() WHERE purchase_id=$1", purchase_id, text)
    await conn.execute("UPDATE purchase SET status='answered', payout_status='eligible', updated_at=now() WHERE id=$1", purchase_id)
    await _ledger(conn, purchase_id, "provider_payable", p["provider_payable_minor"], p["currency"])
    title = await conn.fetchval("SELECT s.title FROM question q JOIN service s ON s.id=q.service_id WHERE q.purchase_id=$1", purchase_id)
    await notifications.notify(conn, p["buyer_id"], "question.answered", {"title": title})
    await audit.record(conn, provider_id, "question.answered", "purchase", purchase_id)


async def expire(conn) -> None:
    """Unanswered questions past due are refunded in full; packages past expiry refund unused sessions."""
    for r in await conn.fetch("SELECT p.* FROM purchase p JOIN question q ON q.purchase_id=p.id WHERE p.kind='question' AND p.status='active' AND q.due_at < now()"):
        await money.provider().refund(r["external_ref"], r["gross_minor"])
        await _ledger(conn, r["id"], "refund", -r["gross_minor"], r["currency"], "unanswered")
        await conn.execute("UPDATE purchase SET status='refunded', refund_minor=gross_minor, updated_at=now() WHERE id=$1", r["id"])
        await notifications.notify(conn, r["buyer_id"], "question.refunded", {"refund_minor": r["gross_minor"]})
    for r in await conn.fetch("SELECT id FROM purchase WHERE kind='package' AND status='active' AND expires_at < now()"):
        if not await conn.fetchval("SELECT 1 FROM booking WHERE purchase_id=$1 AND status IN ('confirmed','in_progress')", r["id"]):
            await refund_unused(conn, r["id"], "expired")
    # Abandoned checkouts.
    await conn.execute("UPDATE purchase SET status='cancelled', updated_at=now() WHERE status='pending_payment' AND created_at < now() - interval '30 minutes'")
