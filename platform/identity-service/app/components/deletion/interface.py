"""Account deletion, kind A: "Delete my ForKhatri account" (docs/ParentApp/ACCOUNT-DELETION.md).

Order of events, each step durable before the next:

  1. start(): the member is closed (status 'deleted': cannot sign in, every session revoked)
     and a deletion job with one row per registered module is written.
  2. run_job(): every module's internal erase endpoint is called in parallel with that
     module's service key; each answer is stored. A module that fails is retried with
     backoff (the retry loop in main.py), for deletion_retry_window_days, after which the
     job shows on the admin "stuck deletions" list until an admin retries it.
  3. finalize(): only when every module answered done / nothing_to_delete, the database
     function removes every identity row and rewrites the audit log to the tombstone.
     The job keeps the receipt; its member_id is nulled.
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import logging
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.components.governance import interface as governance
from app.config.settings import Settings
from app.errors import DomainError

logger = logging.getLogger(__name__)
SessionFactory = async_sessionmaker[AsyncSession]

# The name identity presents to modules on internal calls (Counsel requires exactly this; the others ignore it).
CALLER_NAME = "identity"
OK_STATUSES = ("done", "nothing_to_delete")
_CLAIM_SECONDS = 120
_tasks: set[asyncio.Task[Any]] = set()

# What identity itself keeps after deletion, shown on the receipt in plain words.
IDENTITY_RETAINED = (
    {
        "kind": "security_log",
        "reason": "Security and audit logs are kept for the legal minimum period with your id replaced by a one-way code. No name, phone, email or text.",
    },
    {
        "kind": "deletion_receipt",
        "reason": "A one-line record that the deletion was done (one-way code, date, counts), so the owner can prove it.",
    },
)


def tombstone_of(settings: Settings, member_id: UUID) -> str:
    return hmac.new(settings.deletion_tombstone_pepper.encode(), str(member_id).encode(), hashlib.sha256).hexdigest()


def _backoff(attempts: int) -> timedelta:
    return timedelta(seconds=min(30 * 2 ** max(attempts - 1, 0), 6 * 3600))


# --------------------------------------------------------------------------- before


async def _live_roles(db: AsyncSession, member_id: UUID) -> int:
    return int(
        await db.scalar(
            text(f"SELECT count(*) FROM governance.role_assignment a WHERE a.member_id = :m AND {governance._LIVE}"),  # noqa: SLF001
            {"m": member_id},
        )
        or 0
    )


async def preview(db: AsyncSession, settings: Settings, member_id: UUID) -> dict[str, Any]:
    names = {r.key: r.name for r in await db.execute(text("SELECT key, name FROM registry.module"))}
    return {
        "modules": [{"key": k, "name": names.get(k, k)} for k in settings.erase_modules],
        "blocked": "admin_role" if await _live_roles(db, member_id) else None,
        "retained": list(IDENTITY_RETAINED),
    }


# --------------------------------------------------------------------------- start


async def start(db: AsyncSession, settings: Settings, member_id: UUID) -> UUID:
    """Close the member, revoke every session and write the job. Idempotent per member."""
    existing = await db.scalar(text("SELECT id FROM identity.deletion_job WHERE member_id = :m"), {"m": member_id})
    if existing:
        return existing
    if await _live_roles(db, member_id):
        raise DomainError(
            "admin_role_held",
            "You hold an administrative role. Ask the samaj to end it first, then you can delete your account.",
            409,
        )
    had_ban = bool(
        await db.scalar(
            text("SELECT 1 FROM governance.suspension WHERE member_id = :m AND kind = 'ban' AND lifted_at IS NULL"),
            {"m": member_id},
        )
    )
    job_id = uuid4()
    await db.execute(
        text(
            "INSERT INTO identity.deletion_job (id, member_id, tombstone, deadline_at, receipt) "
            "VALUES (:id, :m, :t, :deadline, CAST(:r AS jsonb))"
        ),
        {
            "id": job_id,
            "m": member_id,
            "t": tombstone_of(settings, member_id),
            "deadline": datetime.now(UTC) + timedelta(days=settings.deletion_retry_window_days),
            "r": json.dumps({"banned": had_ban}),
        },
    )
    for module in settings.erase_modules:
        await db.execute(
            text("INSERT INTO identity.deletion_job_module (job_id, module_key) VALUES (:j, :k)"),
            {"j": job_id, "k": module},
        )
    await db.execute(
        text("UPDATE identity.member SET status = 'deleted', updated_at = now() WHERE id = :m"), {"m": member_id}
    )
    await db.execute(
        text("UPDATE identity.session SET revoked_at = now() WHERE member_id = :m AND revoked_at IS NULL"),
        {"m": member_id},
    )
    return job_id


def launch(factory: SessionFactory, settings: Settings, job_id: UUID) -> None:
    """Run the job in the background so the browser can show progress while it works."""
    task = asyncio.create_task(_safe_run(factory, settings, job_id))
    _tasks.add(task)
    task.add_done_callback(_tasks.discard)


async def _safe_run(factory: SessionFactory, settings: Settings, job_id: UUID) -> None:
    try:
        await run_job(factory, settings, job_id)
    except Exception:  # noqa: BLE001 - the retry loop picks it up
        logger.exception("account deletion job %s failed unexpectedly", job_id)


# --------------------------------------------------------------------------- run


async def _call_module(
    client: httpx.AsyncClient, settings: Settings, module: str, base_url: str | None, member_id: UUID
) -> tuple[str, dict[str, Any] | None, str | None]:
    """Returns (status, result, error). status is a module status or 'failed'."""
    key = settings.service_keys.get(module)
    if not base_url:
        return "failed", None, "not_configured"
    if not key:
        return "failed", None, "no_service_key"
    try:
        response = await client.post(
            f"{base_url.rstrip('/')}/internal/v1/members/{member_id}/erase",
            headers={"X-ForKhatri-Service": CALLER_NAME, "X-ForKhatri-Service-Key": key},
        )
    except httpx.HTTPError as exc:
        return "failed", None, f"unreachable: {type(exc).__name__}"
    if response.status_code == 404:
        return "failed", None, "endpoint_missing"
    if response.status_code != 200:
        return "failed", None, f"http_{response.status_code}"
    try:
        body = response.json()
    except ValueError:
        return "failed", None, "bad_response"
    status = body.get("status") if isinstance(body, dict) else None
    if status not in (*OK_STATUSES, "partial"):
        return "failed", None, "bad_response"
    return status, body, None


async def run_job(
    factory: SessionFactory, settings: Settings, job_id: UUID, client: httpx.AsyncClient | None = None
) -> dict[str, Any]:
    """One pass: ask every due module in parallel, then finalize if all have confirmed."""
    async with factory() as db:
        row = (
            await db.execute(text("SELECT member_id, status FROM identity.deletion_job WHERE id = :j"), {"j": job_id})
        ).first()
        if row is None or row.status == "done" or row.member_id is None:
            return await status_of(factory, job_id)
        member_id = row.member_id
        claimed = [
            r.module_key
            for r in await db.execute(
                text(
                    "UPDATE identity.deletion_job_module SET status = 'running', attempts = attempts + 1, "
                    "claimed_until = now() + (:s * interval '1 second'), updated_at = now() "
                    "WHERE job_id = :j AND ((status IN ('pending','partial','failed') AND next_attempt_at <= now()) "
                    "OR (status = 'running' AND claimed_until < now())) RETURNING module_key"
                ),
                {"j": job_id, "s": _CLAIM_SECONDS},
            )
        ]
        await db.commit()

    targets = settings.erase_modules
    owns_client = client is None
    http = client or httpx.AsyncClient(timeout=settings.erase_timeout_seconds)
    try:
        answers = await asyncio.gather(*(_call_module(http, settings, m, targets.get(m), member_id) for m in claimed))
    finally:
        if owns_client:
            await http.aclose()

    async with factory() as db:
        for module, (status, result, error) in zip(claimed, answers, strict=True):
            attempts = await db.scalar(
                text("SELECT attempts FROM identity.deletion_job_module WHERE job_id = :j AND module_key = :k"),
                {"j": job_id, "k": module},
            )
            await db.execute(
                text(
                    "UPDATE identity.deletion_job_module SET status = :s, result = CAST(:r AS jsonb), last_error = :e, "
                    "claimed_until = NULL, next_attempt_at = :next, updated_at = now() WHERE job_id = :j AND module_key = :k"
                ),
                {
                    "s": status,
                    "r": json.dumps(result) if result is not None else None,
                    "e": error,
                    "next": datetime.now(UTC) + (timedelta(0) if status in OK_STATUSES else _backoff(attempts or 1)),
                    "j": job_id,
                    "k": module,
                },
            )
            if error:
                logger.warning("deletion %s: module %s failed (%s), attempt %s", job_id, module, error, attempts)
        await db.commit()
        await _finalize_if_ready(db, job_id, member_id)
        await db.commit()
    return await status_of(factory, job_id)


async def _finalize_if_ready(db: AsyncSession, job_id: UUID, member_id: UUID) -> None:
    modules = list(
        await db.execute(
            text("SELECT module_key, status, result FROM identity.deletion_job_module WHERE job_id = :j"), {"j": job_id}
        )
    )
    if any(m.status not in OK_STATUSES for m in modules):
        return
    job = (
        await db.execute(text("SELECT tombstone, receipt FROM identity.deletion_job WHERE id = :j FOR UPDATE"), {"j": job_id})
    ).first()
    counts = (
        await db.execute(text("SELECT identity.finalize_member_deletion(:m, :t)"), {"m": member_id, "t": job.tombstone})
    ).scalar_one()
    prior = job.receipt or {}
    retained = [{"scope": "identity", **r} for r in IDENTITY_RETAINED]
    if prior.get("banned"):
        retained.append(
            {
                "scope": "identity",
                "kind": "safety_record",
                "reason": "A safety record that this account was banned is kept, as the one-way code only, so a ban cannot be escaped by deleting the account.",
            }
        )
    per_module: dict[str, Any] = {}
    for m in modules:
        res = m.result or {}
        per_module[m.module_key] = {
            "status": m.status,
            "deleted": res.get("deleted", {}),
            "files_removed": res.get("files_removed", 0),
        }
        retained += [{"scope": m.module_key, **r} for r in res.get("retained", [])]
    receipt = {
        "tombstone": job.tombstone,
        "completed_at": datetime.now(UTC).isoformat(),
        "modules": per_module,
        "identity": counts,
        "retained": retained,
        "banned": bool(prior.get("banned")),
    }
    await db.execute(
        text(
            "UPDATE identity.deletion_job SET status = 'done', member_id = NULL, completed_at = now(), "
            "receipt = CAST(:r AS jsonb) WHERE id = :j"
        ),
        {"r": json.dumps(receipt), "j": job_id},
    )
    await governance.audit(
        db, actor=None, action="account.deleted", details={"tombstone": job.tombstone, "modules": sorted(per_module)}
    )
    logger.info("account deletion %s completed (tombstone %s)", job_id, job.tombstone[:12])


# --------------------------------------------------------------------------- status


async def status_of(factory: SessionFactory, job_id: UUID) -> dict[str, Any]:
    """Public status for the confirmation page: no member identifier, only progress and the receipt."""
    async with factory() as db:
        job = (
            await db.execute(
                text("SELECT status, receipt, requested_at, completed_at FROM identity.deletion_job WHERE id = :j"),
                {"j": job_id},
            )
        ).first()
        if job is None:
            raise DomainError("not_found", "No such deletion.", 404)
        names = {r.key: r.name for r in await db.execute(text("SELECT key, name FROM registry.module"))}
        modules = [
            {
                "module": m.module_key,
                "name": names.get(m.module_key, m.module_key),
                "status": m.status,
                "attempts": m.attempts,
                "error": m.last_error,
                "deleted": (m.result or {}).get("deleted", {}),
                "files_removed": (m.result or {}).get("files_removed", 0),
            }
            for m in await db.execute(
                text(
                    "SELECT module_key, status, attempts, last_error, result FROM identity.deletion_job_module "
                    "WHERE job_id = :j ORDER BY module_key"
                ),
                {"j": job_id},
            )
        ]
    done = job.status == "done"
    return {
        "status": "done" if done else "closing",
        "account_closed": True,
        "modules": modules,
        "receipt": job.receipt if done else None,
        "requested_at": job.requested_at.isoformat(),
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
    }


# --------------------------------------------------------------------------- retry loop and admin


async def retry_due(factory: SessionFactory, settings: Settings) -> int:
    """Re-run every open job inside its retry window that has a module due, or all modules confirmed."""
    async with factory() as db:
        due = [
            r.id
            for r in await db.execute(
                text(
                    "SELECT j.id FROM identity.deletion_job j WHERE j.status = 'running' AND j.deadline_at > now() AND ("
                    "EXISTS (SELECT 1 FROM identity.deletion_job_module m WHERE m.job_id = j.id AND "
                    "((m.status IN ('pending','partial','failed') AND m.next_attempt_at <= now()) "
                    "OR (m.status = 'running' AND m.claimed_until < now()))) "
                    "OR NOT EXISTS (SELECT 1 FROM identity.deletion_job_module m "
                    "WHERE m.job_id = j.id AND m.status NOT IN ('done','nothing_to_delete')))"
                )
            )
        ]
    for job_id in due:
        await _safe_run(factory, settings, job_id)
    return len(due)


async def retry_loop(factory: SessionFactory, settings: Settings) -> None:
    while True:
        try:
            await retry_due(factory, settings)
        except asyncio.CancelledError:
            raise
        except Exception:  # noqa: BLE001
            logger.exception("deletion retry sweep failed")
        await asyncio.sleep(settings.deletion_retry_interval_seconds)


async def stuck_list(db: AsyncSession) -> list[dict[str, Any]]:
    """Open deletions that need a person: a module keeps failing, or the retry window has passed."""
    jobs = list(
        await db.execute(
            text(
                "SELECT j.id, j.tombstone, j.requested_at, j.deadline_at FROM identity.deletion_job j "
                "WHERE j.status = 'running' AND (j.deadline_at <= now() OR EXISTS (SELECT 1 FROM identity.deletion_job_module m "
                "WHERE m.job_id = j.id AND m.status IN ('failed','partial') AND m.attempts >= 3)) ORDER BY j.requested_at"
            )
        )
    )
    out = []
    for j in jobs:
        modules = [
            {"module": m.module_key, "status": m.status, "attempts": m.attempts, "error": m.last_error}
            for m in await db.execute(
                text(
                    "SELECT module_key, status, attempts, last_error FROM identity.deletion_job_module "
                    "WHERE job_id = :j ORDER BY module_key"
                ),
                {"j": j.id},
            )
        ]
        out.append(
            {
                "job_id": str(j.id),
                "reference": j.tombstone[:12],
                "requested_at": j.requested_at.isoformat(),
                "gave_up": j.deadline_at <= datetime.now(UTC),
                "modules": modules,
            }
        )
    return out


async def admin_retry(db: AsyncSession, settings: Settings, job_id: UUID) -> None:
    job = await db.scalar(text("SELECT status FROM identity.deletion_job WHERE id = :j"), {"j": job_id})
    if job is None:
        raise DomainError("not_found", "No such deletion.", 404)
    if job == "done":
        raise DomainError("already_done", "This deletion is already complete.", 409)
    await db.execute(
        text("UPDATE identity.deletion_job SET deadline_at = now() + (:d * interval '1 day') WHERE id = :j"),
        {"d": settings.deletion_retry_window_days, "j": job_id},
    )
    await db.execute(
        text(
            "UPDATE identity.deletion_job_module SET next_attempt_at = now(), attempts = 0, "
            "status = CASE WHEN status = 'running' THEN 'failed' ELSE status END "
            "WHERE job_id = :j AND status NOT IN ('done','nothing_to_delete')"
        ),
        {"j": job_id},
    )
