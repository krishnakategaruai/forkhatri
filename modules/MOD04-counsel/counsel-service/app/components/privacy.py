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
    pm = await conn.fetchrow("SELECT kind, holder_name, ifsc, last4 FROM payout_method WHERE provider_id=$1", member_id)
    data["payout_method"] = dict(pm) if pm else None
    await audit.record(conn, member_id, "privacy.exported", "member", member_id)
    return data


# --- Deletion ---------------------------------------------------------------------------

async def blockers(conn, member_id: UUID) -> list[str]:
    out = []
    if await conn.fetchval("SELECT 1 FROM booking WHERE (seeker_id=$1 OR provider_id=$1) AND status IN ('pending_payment','confirmed','in_progress') AND ends_at > now()", member_id):
        out.append("upcoming_bookings")
    if await conn.fetchval("SELECT 1 FROM purchase WHERE (buyer_id=$1 OR provider_id=$1) AND status='active'", member_id):
        out.append("open_packages_or_questions")
    if await conn.fetchval("SELECT 1 FROM dispute d JOIN booking b ON b.id=d.booking_id WHERE d.status='open' AND (b.seeker_id=$1 OR b.provider_id=$1)", member_id):
        out.append("open_disputes")
    if await conn.fetchval("SELECT 1 FROM booking WHERE provider_id=$1 AND payout_status='eligible'", member_id):
        out.append("unpaid_earnings")
    return out


async def erase(conn, member_id: UUID, reason: str) -> dict:
    found = await blockers(conn, member_id)
    if found:
        raise DomainError("deletion_blocked", "Finish or cancel what is still open first.", 409, blockers=found)
    # Files on disk: evidence proofs, photos, and files this member uploaded.
    keys = [r["document_url"] for r in await conn.fetch("SELECT document_url FROM provider_evidence WHERE provider_id=$1 AND document_url IS NOT NULL", member_id)]
    keys += [r["storage_key"] for r in await conn.fetch("SELECT storage_key FROM file WHERE owner_id=$1 AND deleted_at IS NULL", member_id)]
    photo = await conn.fetchval("SELECT photo_url FROM provider WHERE member_id=$1", member_id)
    for k in keys:
        try:
            storage.path_for(k).unlink(missing_ok=True)
        except Exception:
            pass
    if photo and photo.startswith("/media/photos/"):
        try:
            storage.path_for("public/photos/" + photo.removeprefix("/media/photos/")).unlink(missing_ok=True)
        except Exception:
            pass
    await conn.execute("UPDATE file SET deleted_at=now() WHERE owner_id=$1 AND deleted_at IS NULL", member_id)
    await conn.execute("UPDATE message SET body='' , kind='system' WHERE sender_id=$1 AND kind IN ('chat','file')", member_id)
    await conn.execute("DELETE FROM note WHERE owner_id=$1", member_id)
    await conn.execute("DELETE FROM saved_provider WHERE member_id=$1 OR provider_id=$1", member_id)
    await conn.execute("DELETE FROM notification WHERE member_id=$1", member_id)
    await conn.execute("DELETE FROM delivery WHERE member_id=$1", member_id)
    await conn.execute("DELETE FROM block WHERE member_id=$1 OR blocked_id=$1", member_id)
    await conn.execute("DELETE FROM time_request WHERE seeker_id=$1 OR provider_id=$1", member_id)
    await conn.execute("UPDATE review SET body='' WHERE reviewer_id=$1", member_id)
    # Provider side: the profile disappears from Counsel; paid history stays in the ledger.
    if await conn.fetchval("SELECT 1 FROM provider WHERE member_id=$1", member_id):
        await conn.execute("UPDATE service SET status='archived' WHERE provider_id=$1", member_id)
        await conn.execute("DELETE FROM provider_evidence WHERE provider_id=$1", member_id)
        await conn.execute("DELETE FROM verification WHERE provider_id=$1", member_id)
        await conn.execute("DELETE FROM availability_rule WHERE provider_id=$1", member_id)
        await conn.execute("DELETE FROM availability_exception WHERE provider_id=$1", member_id)
        await conn.execute("DELETE FROM payout_method WHERE provider_id=$1", member_id)
        await conn.execute("DELETE FROM provider_expertise WHERE provider_id=$1", member_id)
        await conn.execute("DELETE FROM search_impression WHERE provider_id=$1", member_id)
        await conn.execute("DELETE FROM profile_view WHERE provider_id=$1", member_id)
        await conn.execute(
            "UPDATE provider SET headline='', intro='', photo_url=NULL, city=NULL, links='{}'::jsonb, status='suspended', review_note='deleted', available_until=NULL WHERE member_id=$1",
            member_id)
    await conn.execute("UPDATE booking SET brief='' WHERE seeker_id=$1", member_id)
    await conn.execute("UPDATE member SET display_name=$2 WHERE member_id=$1", member_id, DELETED_NAME)
    await conn.execute("INSERT INTO erased_member (member_id, reason) VALUES ($1,$2) ON CONFLICT (member_id) DO UPDATE SET erased_at=now(), reason=$2", member_id, reason)
    await audit.record(conn, member_id, "privacy.erased", "member", member_id, {"reason": reason})
    return {"erased": True}


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
