"""Account deletion orchestrator (kind A) against the real database and a stub module server.

Uses a throwaway member that is created and (if the test fails midway) removed here;
other members are never touched. Skipped unless IDENTITY_DB_TESTS=1:
    $env:IDENTITY_DB_TESTS = "1"; .venv\\Scripts\\python -m pytest tests/integration/test_account_deletion.py
"""

from __future__ import annotations

import os
from uuid import UUID, uuid4

import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.components.deletion import interface as deletion
from app.components.governance import interface as gov
from app.config.settings import Settings
from app.errors import DomainError

pytestmark = pytest.mark.skipif(os.environ.get("IDENTITY_DB_TESTS") != "1", reason="IDENTITY_DB_TESTS is not 1")


def make_settings() -> Settings:
    return Settings(
        service_keys={"alpha": "k-alpha", "beta": "k-beta"},
        erase_module_api_urls={"alpha": "http://alpha.test", "beta": "http://beta.test"},
        module_api_urls={},
        admin_module_api_urls={},
    )


class Stub:
    """A module server: erase answers per module, recording every call and the headers sent."""

    def __init__(self) -> None:
        self.answers: dict[str, httpx.Response] = {}
        self.calls: list[tuple[str, str, str]] = []

    def handler(self, request: httpx.Request) -> httpx.Response:
        module = request.url.host.split(".")[0]
        self.calls.append((module, request.url.path, request.headers.get("x-forkhatri-service-key", "")))
        return self.answers[module]


def ok(module: str, status: str = "done") -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "module": module,
            "status": status,
            "deleted": {"posts": 2},
            "retained": [{"kind": "payment_record", "reason": "law"}] if module == "beta" else [],
            "files_removed": 1,
        },
    )


@pytest.fixture
async def factory():
    engine = create_async_engine(Settings().sqlalchemy_url)
    yield async_sessionmaker(engine, expire_on_commit=False)
    await engine.dispose()


@pytest.fixture
async def owner_factory():
    """Cleanup only: the runtime role has no DELETE grants (by design)."""
    s = Settings()
    url = f"postgresql+asyncpg://identity_owner:identity_owner_dev_password@{s.db_host}:{s.db_port}/{s.db_name}"
    engine = create_async_engine(url)
    yield async_sessionmaker(engine, expire_on_commit=False)
    await engine.dispose()


@pytest.fixture
async def member(factory, owner_factory):
    member_id = uuid4()
    phone = "+9171" + str(member_id.int)[:8]
    async with factory() as db:
        await db.execute(
            text("INSERT INTO identity.member (id, display_name, phone_e164) VALUES (:i, 'Throwaway Orchestrator', :p)"),
            {"i": member_id, "p": phone},
        )
        await db.execute(
            text("INSERT INTO identity.session (member_id, token_hash, auth_method, expires_at) VALUES (:i, :h, 'dev', now() + interval '1 day')"),
            {"i": member_id, "h": uuid4().bytes},
        )
        await gov.audit(db, actor=member_id, action="member.contact_viewed", target=member_id, note="a free-text note")
        await db.commit()
    yield member_id
    async with owner_factory() as db:  # leftover only if a test failed before finalizing
        await db.execute(text("DELETE FROM identity.deletion_job_module WHERE job_id IN (SELECT id FROM identity.deletion_job WHERE member_id = :i)"), {"i": member_id})
        await db.execute(text("DELETE FROM identity.deletion_job WHERE member_id = :i"), {"i": member_id})
        await db.execute(text("SELECT identity.finalize_member_deletion(:i, :t)"), {"i": member_id, "t": "test-cleanup-" + str(member_id)})
        await db.commit()


async def member_rows(factory, member_id: UUID) -> int:
    async with factory() as db:
        return int(await db.scalar(text("SELECT count(*) FROM identity.member WHERE id = :i"), {"i": member_id}))


async def test_failing_module_keeps_identity_then_completes(factory, member):
    settings = make_settings()
    stub = Stub()
    stub.answers = {"alpha": ok("alpha"), "beta": httpx.Response(404)}
    client = httpx.AsyncClient(transport=httpx.MockTransport(stub.handler))

    async with factory() as db:
        job_id = await deletion.start(db, settings, member)
        await db.commit()
        # Closed at once: no active session, status deleted.
        assert await db.scalar(text("SELECT status::text FROM identity.member WHERE id = :i"), {"i": member}) == "deleted"
        assert await db.scalar(text("SELECT count(*) FROM identity.session WHERE member_id = :i AND revoked_at IS NULL"), {"i": member}) == 0

    first = await deletion.run_job(factory, settings, job_id, client)
    assert first["status"] == "closing"
    by = {m["module"]: m for m in first["modules"]}
    assert by["alpha"]["status"] == "done"
    assert by["beta"]["status"] == "failed" and by["beta"]["error"] == "endpoint_missing"
    assert await member_rows(factory, member) == 1  # identity stays until every module confirms
    assert all(call[2] == f"k-{call[0]}" for call in stub.calls)  # each module gets its own key

    # Backoff: an immediate second pass makes no new call.
    calls_before = len(stub.calls)
    await deletion.run_job(factory, settings, job_id, client)
    assert len(stub.calls) == calls_before

    # Module becomes ready; admin retry makes it due now.
    stub.answers["beta"] = ok("beta")
    async with factory() as db:
        await deletion.admin_retry(db, settings, job_id)
        await db.commit()
    done = await deletion.run_job(factory, settings, job_id, client)
    assert done["status"] == "done"
    assert done["receipt"]["modules"]["alpha"]["deleted"] == {"posts": 2}
    assert {"scope": "beta", "kind": "payment_record", "reason": "law"} in done["receipt"]["retained"]
    assert await member_rows(factory, member) == 0
    tomb = done["receipt"]["tombstone"]
    assert tomb == deletion.tombstone_of(settings, member)

    async with factory() as db:
        audit = (await db.execute(text("SELECT actor_member_id, target_member_id, actor_tombstone, target_tombstone, note FROM governance.audit_event WHERE actor_tombstone = :t"), {"t": tomb})).first()
        assert audit.actor_member_id is None and audit.target_member_id is None
        assert audit.target_tombstone == tomb and audit.note is None
        assert await db.scalar(text("SELECT count(*) FROM identity.session WHERE member_id = :i"), {"i": member}) == 0
        assert await db.scalar(text("SELECT member_id FROM identity.deletion_job WHERE id = :j"), {"j": job_id}) is None

    # Idempotent: running a finished job changes nothing and calls nobody.
    calls_before = len(stub.calls)
    again = await deletion.run_job(factory, settings, job_id, client)
    assert again["status"] == "done" and len(stub.calls) == calls_before
    await client.aclose()


async def test_partial_answer_is_retried_not_finalized(factory, member):
    settings = make_settings()
    stub = Stub()
    stub.answers = {"alpha": ok("alpha"), "beta": ok("beta", "partial")}
    client = httpx.AsyncClient(transport=httpx.MockTransport(stub.handler))
    async with factory() as db:
        job_id = await deletion.start(db, settings, member)
        await db.commit()
    result = await deletion.run_job(factory, settings, job_id, client)
    assert result["status"] == "closing"
    assert {m["module"]: m["status"] for m in result["modules"]} == {"alpha": "done", "beta": "partial"}
    assert await member_rows(factory, member) == 1
    async with factory() as db:
        stuck = await deletion.stuck_list(db)
        assert all(s["job_id"] != str(job_id) for s in stuck)  # one attempt: not stuck yet
    await client.aclose()


async def test_admin_role_blocks_deletion(factory, owner_factory, member):
    async with factory() as db:
        await db.execute(
            text(
                "INSERT INTO governance.role_assignment (member_id, role, scope_kind, grant_note) "
                "VALUES (:i, 'owner', 'platform', 'test appointment')"
            ),
            {"i": member},
        )
        await db.commit()
    try:
        async with factory() as db:
            with pytest.raises(DomainError) as err:
                await deletion.start(db, make_settings(), member)
            assert err.value.code == "admin_role_held"
    finally:
        async with owner_factory() as db:
            await db.execute(text("DELETE FROM governance.role_assignment WHERE member_id = :i"), {"i": member})
            await db.commit()
