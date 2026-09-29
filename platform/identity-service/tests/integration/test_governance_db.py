"""Admin & Governance Console rules against the real database (migration 005).

Every test runs inside one transaction that is rolled back, so nothing it creates
(members, suspensions, appointments, audit rows) is left in the shared development
database. Needs the development seed (seed_dev_members.py + seed_dev_governance.py):
the president (Ramesh Khatri) and secretary (Meena Khatri) are the real actors.

Skipped unless IDENTITY_DB_TESTS=1:
    $env:IDENTITY_DB_TESTS = "1"; .venv\\Scripts\\python -m pytest tests/integration/test_governance_db.py
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.components.governance import interface as gov
from app.config.settings import Settings
from app.errors import DomainError

pytestmark = pytest.mark.skipif(os.environ.get("IDENTITY_DB_TESTS") != "1", reason="IDENTITY_DB_TESTS is not 1")

OWNER = UUID("a0000000-0000-4000-8000-000000000001")
PRESIDENT = UUID("a0000000-0000-4000-8000-000000000011")
SECRETARY = UUID("a0000000-0000-4000-8000-000000000012")
IP = "127.0.0.1"


@pytest.fixture
async def db() -> AsyncIterator[AsyncSession]:
    engine = create_async_engine(Settings().sqlalchemy_url)
    async with engine.connect() as conn:
        outer = await conn.begin()
        session = AsyncSession(bind=conn, join_transaction_mode="create_savepoint", expire_on_commit=False)
        try:
            yield session
        finally:
            await session.close()
            await outer.rollback()
    await engine.dispose()


async def admin(db: AsyncSession, member_id: UUID) -> gov.Admin:
    return await gov.load_admin(db, member_id, "test")


async def new_member(db: AsyncSession, name: str = "Suresh Khatri") -> UUID:
    member_id = uuid4()
    phone = "+9170" + str(member_id.int)[:8]
    await db.execute(
        text("INSERT INTO identity.member (id, display_name, phone_e164) VALUES (:id, :n, :p)"),
        {"id": member_id, "n": name, "p": phone},
    )
    await db.execute(
        text(
            "INSERT INTO identity.session (member_id, token_hash, auth_method, expires_at) "
            "VALUES (:m, :h, 'password', now() + interval '1 day')"
        ),
        {"m": member_id, "h": uuid4().bytes + uuid4().bytes},
    )
    return member_id


async def status_of(db: AsyncSession, member_id: UUID) -> str:
    return await db.scalar(text("SELECT status::text FROM identity.member WHERE id = :m"), {"m": member_id})


async def live_sessions(db: AsyncSession, member_id: UUID) -> int:
    return await db.scalar(
        text("SELECT count(*) FROM identity.session WHERE member_id = :m AND revoked_at IS NULL"), {"m": member_id}
    )


async def test_president_permissions_cover_only_modules_that_exist(db: AsyncSession) -> None:
    president = await admin(db, PRESIDENT)
    assert president.can("members.suspend") and president.can("approvals.decide")
    assert not president.can("modules.manage") and not president.can("members.contact")
    assert {"mangaly.moderate", "milavn.moderate"} <= president.module_scopes
    assert not any(s.startswith(("counsel.", "finance.", "payments.")) for s in president.module_scopes)
    assert not (await admin(db, uuid4())).is_admin


async def test_suspension_ends_sessions_and_is_audited_then_lifted(db: AsyncSession) -> None:
    target = await new_member(db)
    president = await admin(db, PRESIDENT)
    await gov.suspend(db, president, target, reason_code="harassment", note="Repeated abusive messages.", days=7, ip=IP)
    assert await status_of(db, target) == "suspended"
    assert await live_sessions(db, target) == 0
    actions = [e["action"] for e in (await gov.audit_log(db, target=target))["events"]]
    assert actions == ["member.suspended"]

    await gov.lift(db, president, target, note="Apologised; first offence.", ip=IP)
    assert await status_of(db, target) == "active"


async def test_suspension_needs_reason_and_a_known_length(db: AsyncSession) -> None:
    target = await new_member(db)
    president = await admin(db, PRESIDENT)
    with pytest.raises(DomainError, match="reason"):
        await gov.suspend(db, president, target, reason_code="made_up", note="x x x", days=7, ip=IP)
    with pytest.raises(DomainError):
        await gov.suspend(db, president, target, reason_code="spam", note="", days=7, ip=IP)
    with pytest.raises(DomainError):
        await gov.suspend(db, president, target, reason_code="spam", note="Bulk messages.", days=5, ip=IP)


async def test_nobody_acts_on_themselves_or_on_an_owner(db: AsyncSession) -> None:
    president = await admin(db, PRESIDENT)
    with pytest.raises(DomainError) as self_action:
        await gov.suspend(db, president, PRESIDENT, reason_code="other", note="Testing myself.", days=1, ip=IP)
    assert self_action.value.code == "admin_self_action"
    with pytest.raises(DomainError) as owner:
        await gov.suspend(db, president, OWNER, reason_code="other", note="Testing the owner.", days=1, ip=IP)
    assert owner.value.code == "admin_target_owner"


async def test_ban_needs_a_second_person(db: AsyncSession) -> None:
    target = await new_member(db)
    president = await admin(db, PRESIDENT)
    request = await gov.propose_ban(db, president, target, reason_code="fraud_scam", note="Took money from three families.", ip=IP)
    assert request["status"] == "approval_required"
    assert await status_of(db, target) == "active"

    with pytest.raises(DomainError) as same_person:
        await gov.decide_approval(db, president, UUID(request["approval_id"]), decision="approved", note=None, ip=IP)
    assert same_person.value.code == "approval_four_eyes"

    secretary = await admin(db, SECRETARY)
    decided = await gov.decide_approval(db, secretary, UUID(request["approval_id"]), decision="approved", note=None, ip=IP)
    assert decided["status"] == "approved"
    assert await status_of(db, target) == "suspended"
    open_kind = await db.scalar(text("SELECT kind FROM governance.suspension WHERE member_id = :m AND lifted_at IS NULL"), {"m": target})
    assert open_kind == "ban"


async def test_sensitive_role_needs_approval_and_then_reaches_modules(db: AsyncSession) -> None:
    target = await new_member(db, "Kiran Khatri")
    president = await admin(db, PRESIDENT)
    result = await gov.grant_role(
        db, president, member_id=target, role="grievance_officer", scope_key=None, title=None,
        ends_at=datetime.now(UTC) + timedelta(days=365), note="Elected at the annual meeting.", ip=IP,
    )
    assert result["status"] == "approval_required"
    assert await gov.module_scopes_for(db, target) == []

    secretary = await admin(db, SECRETARY)
    await gov.decide_approval(db, secretary, UUID(result["approval_id"]), decision="approved", note=None, ip=IP)
    assert "mangaly.moderate" in await gov.module_scopes_for(db, target)

    with pytest.raises(DomainError) as owner_grant:
        await gov.grant_role(db, president, member_id=target, role="owner", scope_key=None, title=None, ends_at=None, note="Try it.", ip=IP)
    assert owner_grant.value.code == "admin_forbidden"


async def test_module_moderator_is_granted_directly(db: AsyncSession) -> None:
    target = await new_member(db, "Pooja Khatri")
    president = await admin(db, PRESIDENT)
    result = await gov.grant_role(
        db, president, member_id=target, role="moderator", scope_key="mangaly", title=None, ends_at=None,
        note="Volunteer moderator for Mangaly.", ip=IP,
    )
    assert result["status"] == "granted"
    assert await gov.module_scopes_for(db, target) == ["mangaly.moderate"]
    await gov.revoke_role(db, president, UUID(result["assignment_id"]), note="Term finished early.", ip=IP)
    assert await gov.module_scopes_for(db, target) == []


async def test_chapter_head_appoints_only_inside_their_chapter(db: AsyncSession) -> None:
    head = await new_member(db, "Anil Khatri")
    helper = await new_member(db, "Sunita Khatri")
    president = await admin(db, PRESIDENT)
    await gov.grant_role(
        db, president, member_id=head, role="chapter_head", scope_key="telangana-hyderabad", title="Hyderabad convenor",
        ends_at=None, note="Chosen by the Hyderabad members.", ip=IP,
    )
    chapter_head = await admin(db, head)
    assert chapter_head.managed_chapters == frozenset({"telangana-hyderabad"})
    granted = await gov.grant_role(
        db, chapter_head, member_id=helper, role="chapter_secretary", scope_key="telangana-hyderabad", title=None,
        ends_at=None, note="Keeps the chapter's records.", ip=IP,
    )
    assert granted["status"] == "granted"
    with pytest.raises(DomainError):
        await gov.grant_role(
            db, chapter_head, member_id=helper, role="chapter_secretary", scope_key="telangana-warangal", title=None,
            ends_at=None, note="Not my chapter.", ip=IP,
        )


async def test_timed_suspension_ends_on_its_own(db: AsyncSession) -> None:
    target = await new_member(db)
    await db.execute(text("UPDATE identity.member SET status = 'suspended' WHERE id = :m"), {"m": target})
    await db.execute(
        text(
            "INSERT INTO governance.suspension (member_id, kind, reason_code, note, starts_at, ends_at) "
            "VALUES (:m, 'suspension', 'spam', 'Posted adverts.', now() - interval '2 days', now() - interval '1 minute')"
        ),
        {"m": target},
    )
    assert await gov.expire_due_suspensions(db) >= 1
    assert await status_of(db, target) == "active"


async def test_audit_log_cannot_be_rewritten(db: AsyncSession) -> None:
    await gov.audit(db, actor=PRESIDENT, action="test.audit_probe", note="probe")
    with pytest.raises(Exception, match="append-only|permission denied"):
        async with db.begin_nested():
            await db.execute(text("UPDATE governance.audit_event SET note = 'changed' WHERE action = 'test.audit_probe'"))
