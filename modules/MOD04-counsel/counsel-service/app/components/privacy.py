"""Privacy: a member's own data export, deletion of their Counsel data, and
retention clean-up of consultation files and recordings.

Deletion rules (product definition §34, §61):
  * Refused while the member has a live paid booking, an unanswered paid
    question, or an active package — those must end first, so nobody loses
    money or a promised consultation.
  * Personal and consultation-private data is removed: provider profile,
    evidence and proof documents, payout details, private notes, their
    uploaded files, messages they wrote, saved people, notifications.
  * Financial and audit records stay (tax and dispute law), with the member
    shown as "Deleted member". Reviews they wrote stay without their name.
"""

from __future__ import annotations

import base64
import hashlib
import json
from datetime import datetime, timedelta, timezone
from uuid import UUID

from cryptography.fernet import Fernet

from app.components import audit, money, storage
from app.errors import DomainError
from app.settings import get_settings

DELETED_NAME = "Deleted member"


# --- Payout details (encrypted at rest) ------------------------------------------------

def _fernet() -> Fernet:
    key = get_settings().payout_encryption_key
    if not key or "CHANGE_ME" in key:
        # Development fallback derived from the service key: never used in a real deployment,
        # where PAYOUT_ENCRYPTION_KEY must be set (checked in main at start-up).
        key = base64.urlsafe_b64encode(hashlib.sha256(("counsel-dev:" + get_settings().platform_service_key).encode()).digest()).decode()
    return Fernet(key.encode())


def encrypt(value: str) -> str:
    return _fernet().encrypt(value.encode()).decode()


def decrypt(token: str) -> str:
    return _fernet().decrypt(token.encode()).decode()


# --- Export ------------------------------------------------------------------------------

async def export(conn, member_id: UUID) -> dict:
    def rows(rs):
        out = []
        for r in rs:
            d = dict(r)
            for k, v in d.items():
                if isinstance(v, (datetime,)):
                    d[k] = v.isoformat()
                elif isinstance(v, UUID):
                    d[k] = str(v)
            out.append(d)
        return out

    data: dict = {"exported_at": datetime.now(timezone.utc).isoformat(), "member_id": str(member_id)}
    data["provider_profile"] = rows(await conn.fetch("SELECT * FROM provider WHERE member_id=$1", member_id))
    data["expertise"] = rows(await conn.fetch("SELECT * FROM provider_expertise WHERE provider_id=$1", member_id))
    data["evidence"] = rows(await conn.fetch("SELECT id, kind, title, issuer, year_from, year_to, status, document_name, created_at FROM provider_evidence WHERE provider_id=$1", member_id))
    data["services"] = rows(await conn.fetch("SELECT * FROM service WHERE provider_id=$1", member_id))
    data["bookings"] = rows(await conn.fetch(
        "SELECT id, service_title, starts_at, ends_at, status, brief, gross_minor, refund_minor, currency, CASE WHEN seeker_id=$1 THEN 'booked' ELSE 'consulted' END AS role "
        "FROM booking WHERE seeker_id=$1 OR provider_id=$1 ORDER BY starts_at", member_id))
    data["messages_sent"] = rows(await conn.fetch("SELECT booking_id, body, created_at FROM message WHERE sender_id=$1 AND kind='chat' ORDER BY id", member_id))
    data["private_notes"] = rows(await conn.fetch("SELECT booking_id, body, updated_at FROM note WHERE owner_id=$1", member_id))
    data["reviews_written"] = rows(await conn.fetch("SELECT booking_id, overall, body, created_at FROM review WHERE reviewer_id=$1", member_id))
    data["purchases"] = rows(await conn.fetch("SELECT id, kind, status, gross_minor, refund_minor, currency, created_at FROM purchase WHERE buyer_id=$1 OR provider_id=$1", member_id))
    data["questions"] = rows(await conn.fetch(
        "SELECT q.body, q.answer, q.created_at FROM question q JOIN purchase p ON p.id=q.purchase_id WHERE p.buyer_id=$1 OR p.provider_id=$1", member_id))
    data["badges"] = rows(await conn.fetch("SELECT badge_id, level, awarded_at FROM badge_award WHERE provider_id=$1", member_id))
    data["saved_people"] = rows(await conn.fetch("SELECT provider_id, created_at FROM saved_provider WHERE member_id=$1", member_id))
    data["member_record"] = rows(await conn.fetch("SELECT member_id, display_name, language, timezone, first_seen, last_seen FROM member WHERE member_id=$1", member_id))
    data["availability_rules"] = rows(await conn.fetch("SELECT weekday, start_time::text, end_time::text, kind FROM availability_rule WHERE provider_id=$1", member_id))
    data["availability_exceptions"] = rows(await conn.fetch("SELECT on_date, start_time::text, end_time::text, available, note FROM availability_exception WHERE provider_id=$1", member_id))
    data["verifications"] = rows(await conn.fetch("SELECT dimension, verified_at, note FROM verification WHERE provider_id=$1", member_id))
    data["packages"] = rows(await conn.fetch("SELECT p.* FROM package p JOIN service s ON s.id=p.service_id WHERE s.provider_id=$1", member_id))
    data["payouts"] = rows(await conn.fetch("SELECT id, amount_minor, currency, status, created_at, paid_at FROM payout WHERE provider_id=$1", member_id))
    data["files_uploaded"] = rows(await conn.fetch("SELECT id, booking_id, name, mime, size_bytes, is_recording, created_at FROM file WHERE owner_id=$1 AND deleted_at IS NULL", member_id))
    data["action_items"] = rows(await conn.fetch("SELECT booking_id, text, done, created_at FROM action_item WHERE owner_id=$1 OR created_by=$1", member_id))
    data["time_requests"] = rows(await conn.fetch("SELECT service_id, starts_at, brief, note, status, reply, created_at FROM time_request WHERE seeker_id=$1 OR provider_id=$1", member_id))
    data["notifications"] = rows(await conn.fetch("SELECT kind, params, read_at, created_at FROM notification WHERE member_id=$1", member_id))
    data["blocks"] = rows(await conn.fetch("SELECT blocked_id, created_at FROM block WHERE member_id=$1", member_id))
    data["call_feedback"] = rows(await conn.fetch("SELECT booking_id, good, issues, created_at FROM call_feedback WHERE member_id=$1", member_id))
    data["recording_consents"] = rows(await conn.fetch("SELECT booking_id, consented_at FROM recording_consent WHERE member_id=$1", member_id))
    data["disputes_opened"] = rows(await conn.fetch("SELECT booking_id, reason, status, created_at FROM dispute WHERE opened_by=$1", member_id))
    data["reports_filed"] = rows(await conn.fetch("SELECT target_kind, reason, detail, status, created_at FROM report WHERE reporter_id=$1", member_id))
    data["expertise_requests"] = rows(await conn.fetch("SELECT name, note, status, created_at FROM expertise_request WHERE proposed_by=$1", member_id))
    pm = await conn.fetchrow("SELECT kind, holder_name, ifsc, last4 FROM payout_method WHERE provider_id=$1", member_id)
    data["payout_method"] = dict(pm) if pm else None
    await audit.record(conn, member_id, "privacy.exported", "member", member_id)
    return data


# --- Deletion ---------------------------------------------------------------------------
# Contract: docs/ParentApp/ACCOUNT-DELETION.md. Immediate, transactional, idempotent.
# Inventory and per-table actions: modules/MOD04-counsel/ACCOUNT-DELETION.md.

def tombstone(member_id: UUID) -> UUID:
    """One-way stand-in id for a deleted member. Retained rows (money, safety, other
    people's consultations) point at this id, never at the real one."""
    h = hashlib.sha256(f"counsel-erased:{member_id}:{get_settings().platform_service_key}".encode()).digest()
    return UUID(bytes=h[:16], version=4)


# Every table/column that can hold a member id. Used to detect "is there anything to delete".
MEMBER_COLUMNS: dict[str, tuple[str, ...]] = {
    "member": ("member_id",), "provider": ("member_id",), "booking": ("seeker_id", "provider_id"),
    "purchase": ("buyer_id", "provider_id"), "payout": ("provider_id",), "review": ("reviewer_id", "provider_id"),
    "message": ("sender_id",), "note": ("owner_id",), "action_item": ("owner_id", "created_by"),
    "file": ("owner_id",), "call_feedback": ("member_id",), "recording_consent": ("member_id",), "session_event": ("member_id",),
    "dispute": ("opened_by",), "report": ("reporter_id",), "notification": ("member_id",),
    "delivery": ("member_id",), "block": ("member_id", "blocked_id"), "saved_provider": ("member_id", "provider_id"),
    "time_request": ("seeker_id", "provider_id"), "expertise_request": ("proposed_by",),
}


async def _count(conn, sql: str, *args) -> int:
    return int((await conn.execute(sql, *args)).split()[-1])


async def _has_anything(conn, member_id: UUID) -> bool:
    for table, cols in MEMBER_COLUMNS.items():
        cond = " OR ".join(f"{c}=$1" for c in cols)
        if await conn.fetchval(f"SELECT 1 FROM {table} WHERE {cond} LIMIT 1", member_id):
            return True
    return False


async def blockers(conn, member_id: UUID) -> list[str]:
    """Deletion is immediate and never refused. These are what the member should KNOW will be
    closed for them (shown as a warning before they confirm); none of them blocks deletion."""
    out = []
    if await conn.fetchval("SELECT 1 FROM booking WHERE (seeker_id=$1 OR provider_id=$1) AND status IN ('pending_payment','confirmed','in_progress') AND ends_at > now()", member_id):
        out.append("upcoming_bookings")
    if await conn.fetchval("SELECT 1 FROM purchase WHERE (buyer_id=$1 OR provider_id=$1) AND status IN ('pending_payment','active')", member_id):
        out.append("open_packages_or_questions")
    if await conn.fetchval("SELECT 1 FROM dispute d JOIN booking b ON b.id=d.booking_id WHERE d.status='open' AND (b.seeker_id=$1 OR b.provider_id=$1)", member_id):
        out.append("open_disputes")
    if await conn.fetchval("SELECT 1 FROM booking WHERE provider_id=$1 AND payout_status='eligible'", member_id):
        out.append("unpaid_earnings")
    return out


async def _close_open_work(conn, member_id: UUID, counts: dict) -> None:
    """Future consultations and open packages/questions end now, with the other person told and
    refunds recorded where money was paid."""
    from app.components import bookings, notifications, purchases
    # Under way: as the expert it is refunded in full; as the consumer it counts as held.
    for r in await conn.fetch("SELECT * FROM booking WHERE status='in_progress' AND (seeker_id=$1 OR provider_id=$1) FOR UPDATE", member_id):
        b = dict(r)
        if b["provider_id"] == member_id:
            refunded = 0 if b["purchase_id"] else await bookings._refund(conn, b, 100, "cancelled_by_provider: member_deleted")
            await conn.execute("UPDATE booking SET status='cancelled_by_provider', cancel_reason='member_deleted', cancelled_at=now(), updated_at=now() WHERE id=$1", b["id"])
            await notifications.notify(conn, b["seeker_id"], "booking.cancelled_deleted", {"title": b["service_title"], "refund_minor": refunded}, b["id"])
        else:
            await conn.execute("UPDATE booking SET status='completed', completed_at=now(), payout_status='eligible', updated_at=now() WHERE id=$1", b["id"])
            await notifications.notify(conn, b["provider_id"], "booking.cancelled_deleted", {"title": b["service_title"], "refund_minor": 0}, b["id"])
        counts["bookings"] = counts.get("bookings", 0) + 1
    for r in await conn.fetch("SELECT id FROM booking WHERE status IN ('pending_payment','confirmed') AND (seeker_id=$1 OR provider_id=$1) FOR UPDATE", member_id):
        await bookings.cancel(conn, booking_id=r["id"], actor_id=member_id, reason="member_deleted")
        counts["bookings"] = counts.get("bookings", 0) + 1
    for r in await conn.fetch("SELECT * FROM purchase WHERE status IN ('pending_payment','active') AND (buyer_id=$1 OR provider_id=$1) FOR UPDATE", member_id):
        p = dict(r)
        other = p["provider_id"] if p["buyer_id"] == member_id else p["buyer_id"]
        if p["status"] == "active":
            if p["kind"] == "package":
                await purchases.refund_unused(conn, p["id"], "member_deleted", member_id)
            else:
                await money.provider().refund(p["external_ref"], p["gross_minor"])
                await purchases._ledger(conn, p["id"], "refund", -p["gross_minor"], p["currency"], "member_deleted")
                await conn.execute("UPDATE purchase SET status='refunded', refund_minor=gross_minor, updated_at=now() WHERE id=$1", p["id"])
        else:
            await conn.execute("UPDATE purchase SET status='expired', updated_at=now() WHERE id=$1", p["id"])
        await notifications.notify(conn, other, "purchase.closed_deleted", {"kind": p["kind"]})
        counts["purchases"] = counts.get("purchases", 0) + 1
    for r in await conn.fetch("SELECT seeker_id, provider_id FROM time_request WHERE status='pending' AND (seeker_id=$1 OR provider_id=$1)", member_id):
        other = r["provider_id"] if r["seeker_id"] == member_id else r["seeker_id"]
        await notifications.notify(conn, other, "purchase.closed_deleted", {"kind": "time_request"})


async def _erase_in_tx(conn, member_id: UUID, reason: str) -> tuple[dict, list[str]]:
    """Returns (contract response, file keys to remove from disk after the transaction commits)."""
    t = tombstone(member_id)
    ts = str(t)
    sid = str(member_id)
    await conn.execute("SELECT pg_advisory_xact_lock(hashtext($1))", sid)
    if not await _has_anything(conn, member_id):
        return {"module": "counsel", "status": "nothing_to_delete", "deleted": {}, "retained": [], "files_removed": 0}, []
    deleted: dict[str, int] = {}

    def add(kind: str, n: int) -> None:
        if n:
            deleted[kind] = deleted.get(kind, 0) + n

    # The "Deleted member" stand-in other people see.
    await conn.execute("INSERT INTO member (member_id, display_name) VALUES ($1,$2) ON CONFLICT (member_id) DO NOTHING", t, DELETED_NAME)

    # 1. Future work ends with the other person told and refunds recorded.
    closed: dict = {}
    await _close_open_work(conn, member_id, closed)
    add("future_bookings_cancelled", closed.get("bookings", 0))
    add("open_packages_and_questions_closed", closed.get("purchases", 0))

    # 2. Files on disk: evidence proofs, photo, every file this member uploaded.
    keys = [r["document_url"] for r in await conn.fetch("SELECT document_url FROM provider_evidence WHERE provider_id=$1 AND document_url IS NOT NULL", member_id)]
    keys += [r["storage_key"] for r in await conn.fetch("SELECT storage_key FROM file WHERE owner_id=$1", member_id)]
    photo = await conn.fetchval("SELECT photo_url FROM provider WHERE member_id=$1", member_id)
    if photo and photo.startswith("/media/photos/"):
        keys.append("public/photos/" + photo.removeprefix("/media/photos/"))

    # 3. What the member wrote or owns, in other people's consultations and their own.
    add("messages", await _count(conn, "DELETE FROM message WHERE (sender_id=$1 AND kind IN ('chat','file')) OR file_id IN (SELECT id FROM file WHERE owner_id=$1)", member_id))
    add("files", await _count(conn, "DELETE FROM file WHERE owner_id=$1", member_id))
    add("notes", await _count(conn, "DELETE FROM note WHERE owner_id=$1", member_id))
    add("action_items", await _count(conn, "DELETE FROM action_item WHERE owner_id=$1 OR created_by=$1", member_id))
    add("call_feedback", await _count(conn, "DELETE FROM call_feedback WHERE member_id=$1", member_id))
    add("recording_consents", await _count(conn, "DELETE FROM recording_consent WHERE member_id=$1", member_id))
    add("time_requests", await _count(conn, "DELETE FROM time_request WHERE seeker_id=$1 OR provider_id=$1", member_id))
    add("saved_people", await _count(conn, "DELETE FROM saved_provider WHERE member_id=$1 OR provider_id=$1", member_id))
    add("blocks", await _count(conn, "DELETE FROM block WHERE member_id=$1 OR blocked_id=$1", member_id))
    add("notifications", await _count(conn, "DELETE FROM notification WHERE member_id=$1", member_id))
    add("queued_messages", await _count(conn, "DELETE FROM delivery WHERE member_id=$1", member_id))
    add("reviews_about_me", await _count(conn, "DELETE FROM review WHERE provider_id=$1", member_id))
    add("expertise_requests", await _count(conn, "DELETE FROM expertise_request WHERE proposed_by=$1 AND status='pending'", member_id))
    add("question_texts", await _count(
        conn, "UPDATE question q SET body=CASE WHEN p.buyer_id=$1 THEN '' ELSE q.body END, answer=CASE WHEN p.provider_id=$1 THEN NULL ELSE q.answer END "
              "FROM purchase p WHERE p.id=q.purchase_id AND (p.buyer_id=$1 OR p.provider_id=$1)", member_id))

    # 4. Expert side: profile, documents, availability, payout details leave; rows other people's
    #    consultations or money depend on move to a stripped stand-in provider.
    if await conn.fetchval("SELECT 1 FROM provider WHERE member_id=$1", member_id):
        add("expert_documents", await _count(conn, "DELETE FROM provider_evidence WHERE provider_id=$1", member_id))
        add("payout_details", await _count(conn, "DELETE FROM payout_method WHERE provider_id=$1", member_id))
        add("availability", await _count(conn, "DELETE FROM availability_rule WHERE provider_id=$1", member_id)
            + await _count(conn, "DELETE FROM availability_exception WHERE provider_id=$1", member_id))
        add("expert_profile_parts", await _count(conn, "DELETE FROM verification WHERE provider_id=$1", member_id)
            + await _count(conn, "DELETE FROM provider_expertise WHERE provider_id=$1", member_id)
            + await _count(conn, "DELETE FROM badge_award WHERE provider_id=$1", member_id)
            + await _count(conn, "DELETE FROM search_impression WHERE provider_id=$1", member_id)
            + await _count(conn, "DELETE FROM profile_view WHERE provider_id=$1", member_id))
        used = ("(SELECT service_id FROM booking WHERE provider_id=$1 UNION SELECT service_id FROM purchase WHERE provider_id=$1 "
                "UNION SELECT q.service_id FROM question q JOIN purchase p ON p.id=q.purchase_id WHERE p.provider_id=$1)")
        add("services", await _count(conn, f"DELETE FROM service WHERE provider_id=$1 AND id NOT IN {used}", member_id))
        keep = await conn.fetchval("SELECT EXISTS (SELECT 1 FROM booking WHERE provider_id=$1) OR EXISTS (SELECT 1 FROM purchase WHERE provider_id=$1) OR EXISTS (SELECT 1 FROM payout WHERE provider_id=$1)", member_id)
        if keep:
            await conn.execute(
                "INSERT INTO provider (member_id, headline, intro, photo_url, city, country, timezone, languages, links, currency, status, review_note, standing) "
                "SELECT $2, '', '', NULL, NULL, country, timezone, '{}', '{}'::jsonb, currency, 'suspended', 'deleted', standing FROM provider WHERE member_id=$1 "
                "ON CONFLICT (member_id) DO NOTHING", member_id, t)
            await conn.execute("UPDATE service SET provider_id=$2, description='', outcomes='{}', status='archived' WHERE provider_id=$1", member_id, t)
            add("packages", await _count(conn, "DELETE FROM package WHERE service_id IN (SELECT id FROM service WHERE provider_id=$1) AND id NOT IN (SELECT package_id FROM purchase WHERE package_id IS NOT NULL)", t))
            for tbl in ("booking", "purchase", "payout"):
                await conn.execute(f"UPDATE {tbl} SET provider_id=$2 WHERE provider_id=$1", member_id, t)
        add("expert_profile", await _count(conn, "DELETE FROM provider WHERE member_id=$1", member_id))

    # 5. Consumer side and shared rows that must stay for other people or for the law: point at the stand-in.
    await conn.execute("UPDATE booking SET seeker_id=$2, brief='' WHERE seeker_id=$1", member_id, t)
    await conn.execute("UPDATE booking SET cancelled_by=$2 WHERE cancelled_by=$1", member_id, t)
    await conn.execute("UPDATE purchase SET buyer_id=$2 WHERE buyer_id=$1", member_id, t)
    await conn.execute("UPDATE message SET sender_id=$2 WHERE sender_id=$1", member_id, t)
    await conn.execute("UPDATE note SET updated_by=$2 WHERE updated_by=$1", member_id, t)
    await conn.execute("UPDATE session_event SET member_id=$2 WHERE member_id=$1", member_id, t)
    await conn.execute("UPDATE review SET reviewer_id=$2, body='' WHERE reviewer_id=$1", member_id, t)
    await conn.execute("UPDATE dispute SET opened_by=$2, reason='' WHERE opened_by=$1", member_id, t)
    await conn.execute("UPDATE dispute SET decided_by=$2 WHERE decided_by=$1", member_id, t)
    await conn.execute("UPDATE report SET reporter_id=$2, detail='' WHERE reporter_id=$1", member_id, t)
    await conn.execute("UPDATE report SET target_id=$2, detail='' WHERE target_id=$1", sid, ts)
    await conn.execute("UPDATE report SET decided_by=$2 WHERE decided_by=$1", member_id, t)
    await conn.execute("UPDATE expertise_request SET proposed_by=$2, note='' WHERE proposed_by=$1", member_id, t)
    await conn.execute("UPDATE expertise_request SET decided_by=$2 WHERE decided_by=$1", member_id, t)
    await conn.execute("UPDATE provider SET reviewed_by=$2 WHERE reviewed_by=$1", member_id, t)
    await conn.execute("UPDATE provider_evidence SET reviewed_by=$2 WHERE reviewed_by=$1", member_id, t)
    await conn.execute("UPDATE verification SET verified_by=$2 WHERE verified_by=$1", member_id, t)
    # Audit trail stays for security: the member's id becomes the stand-in and any detail naming them is cleared.
    await conn.execute("UPDATE audit_log SET detail='{}'::jsonb WHERE actor_id=$1 OR target_id=$2 OR detail::text LIKE '%'||$2||'%'", member_id, sid)
    await conn.execute("UPDATE audit_log SET actor_id=$2 WHERE actor_id=$1", member_id, t)
    await conn.execute("UPDATE audit_log SET target_id=$2 WHERE target_id=$1", sid, ts)

    # 6. Money that never moved leaves; consultations between two deleted people end too.
    add("unpaid_payment_attempts", await _count(
        conn, "DELETE FROM payment WHERE status IN ('created','failed') AND booking_id IN (SELECT id FROM booking WHERE seeker_id=$1 OR provider_id=$1)", t))
    add("bookings_between_deleted_members", await _count(
        conn, "DELETE FROM booking b WHERE (b.seeker_id=$1 OR b.provider_id=$1) AND b.seeker_id IN (SELECT member_id FROM erased_member UNION SELECT $1) "
              "AND b.provider_id IN (SELECT member_id FROM erased_member UNION SELECT $1) AND NOT EXISTS (SELECT 1 FROM payment p WHERE p.booking_id=b.id)", t))
    add("member_record", await _count(conn, "DELETE FROM member WHERE member_id=$1", member_id))

    # 7. Receipt and the retained summary.
    await conn.execute("INSERT INTO erased_member (member_id, reason) VALUES ($1,$2) ON CONFLICT (member_id) DO UPDATE SET erased_at=now(), reason=$2", t, reason)
    retained = []
    n = await conn.fetchval("SELECT count(*) FROM booking WHERE seeker_id=$1 OR provider_id=$1", t)
    if n:
        retained.append({"kind": "consultations", "count": n, "reason": "Kept for the other person (their history, disputes and tax records); you appear as Deleted member, with no brief, messages or files of yours."})
    n = await conn.fetchval("SELECT count(*) FROM payment WHERE booking_id IN (SELECT id FROM booking WHERE seeker_id=$1 OR provider_id=$1)", t)
    if n:
        retained.append({"kind": "payments", "count": n, "reason": "Payment and tax records where money moved are kept by law, under an anonymous id."})
    n = await conn.fetchval("SELECT count(*) FROM review WHERE reviewer_id=$1", t)
    if n:
        retained.append({"kind": "ratings", "count": n, "reason": "Star ratings you gave stay in the expert's score, without your name or words."})
    n = await conn.fetchval("SELECT count(*) FROM report WHERE reporter_id=$1 OR target_id=$2", t, ts)
    if n:
        retained.append({"kind": "safety_reports", "count": n, "reason": "A record that a report was made or received, so safety is not lost; no name or text."})
    retained.append({"kind": "deletion_receipt", "reason": "One line (anonymous id, date, counts) to prove the deletion was done."})
    await audit.record(conn, t, "privacy.erased", "member", ts, {"reason": reason, "deleted": deleted})
    return {"module": "counsel", "status": "done", "deleted": deleted, "retained": retained, "files_removed": 0}, keys


async def erase_member(member_id: UUID, reason: str) -> dict:
    """Erase everything Counsel holds about a member (contract: docs/ParentApp/ACCOUNT-DELETION.md).
    Database work is one transaction; files are removed from disk only after it commits."""
    from app import db, identity
    async with db.tx() as conn:
        result, keys = await _erase_in_tx(conn, member_id, reason)
    removed = 0
    for k in keys:
        try:
            p = storage.path_for(k)
            if p.exists():
                p.unlink()
                removed += 1
        except Exception:
            pass
    result["files_removed"] = removed
    identity.forget(member_id)
    return result


async def is_erased(conn, member_id: UUID) -> bool:
    return bool(await conn.fetchval("SELECT 1 FROM erased_member WHERE member_id=$1", member_id))


# --- Retention ------------------------------------------------------------------------------

async def apply_retention(conn) -> int:
    rec_days = int(await money.setting(conn, "retention_recording_days", 90))
    file_days = int(await money.setting(conn, "retention_file_days", 365))
    now = datetime.now(timezone.utc)
    rows = await conn.fetch(
        "SELECT id, storage_key FROM file WHERE deleted_at IS NULL AND ((is_recording AND created_at < $1) OR (NOT is_recording AND created_at < $2))",
        now - timedelta(days=rec_days), now - timedelta(days=file_days))
    for r in rows:
        try:
            storage.path_for(r["storage_key"]).unlink(missing_ok=True)
        except Exception:
            pass
        await conn.execute("UPDATE file SET deleted_at=now() WHERE id=$1", r["id"])
    if rows:
        await audit.record(conn, None, "retention.files_removed", "file", "batch", {"count": len(rows)})
    return len(rows)


def dumps(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, default=str)
