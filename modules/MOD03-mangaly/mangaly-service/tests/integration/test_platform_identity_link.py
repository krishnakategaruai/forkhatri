"""Integration tests: ForKhatri platform claims → member-link row → RLS context.

Real `mangaly` database as the non-owning `mangaly_app` role (migration 014 must
be applied); only the platform Identity & Trust Service is mocked, because it is
a separate service (IMPLEMENTATION-TEST-STANDARDS §4). Every test rolls back.

Traces to: docs/ParentApp/07-tech-reqs.md TR10, TR11, TR15; migration 014.
"""

from __future__ import annotations

import secrets
import uuid
from collections.abc import AsyncIterator, Iterator
from datetime import UTC, datetime, timedelta

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.components.identity_bridge import interface as identity
from app.components.identity_bridge import platform
from app.config.settings import Settings, get_settings
from app.db.engine import create_engine, create_session_factory
from app.db.session import VAR_ACCOUNT_ID, read_session_variable, set_account_context


def random_phone() -> str:
    return "+9170" + "".join(secrets.choice("0123456789") for _ in range(8))


@pytest_asyncio.fixture(scope="module")
async def engine():  # type: ignore[no-untyped-def]
    eng = create_engine()
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def session(engine) -> AsyncIterator[AsyncSession]:  # type: ignore[no-untyped-def]
    async with create_session_factory(engine)() as s:
        yield s


class Claims:
    """Mutable claims the mocked identity service returns for any token."""

    def __init__(self) -> None:
        self.body: dict[str, object] = {}


@pytest.fixture
def platform_claims(monkeypatch: pytest.MonkeyPatch) -> Iterator[Claims]:
    claims = Claims()

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=claims.body)

    monkeypatch.setattr(
        platform,
        "_client",
        httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://identity.test"),
    )
    platform.clear_cache()
    yield claims
    platform.clear_cache()


def member_claims(member_id: uuid.UUID, phone: str | None, email: str | None) -> dict[str, object]:
    return {
        "member_id": str(member_id),
        "display_name": "Integration Member",
        "preferred_language": "en",
        "identity_level": 1,
        "status": "active",
        "session_expires_at": "2026-10-14T00:00:00+00:00",
        "phone_e164": phone,
        "email": email,
    }


async def test_Given_a_new_platform_member_When_resolved_Then_link_row_and_context_exist(
    session: AsyncSession, platform_claims: Claims
) -> None:
    member, phone = uuid.uuid4(), random_phone()
    platform_claims.body = member_claims(member, phone, None)

    async with session.begin():
        resolved = await identity.resolve_platform_session(session, "tok")
        account_id = resolved.account_id

        assert account_id == member
        assert resolved.expires_at is not None
        assert resolved.expires_at.isoformat() == "2026-10-14T00:00:00+00:00"
        assert await read_session_variable(session, VAR_ACCOUNT_ID) == str(member)
        # Home Circle reads these through RLS as the member themself.
        assert await identity.get_own_identifiers(session, account_id=member) == (phone, None)
        row = (
            await session.execute(
                text(
                    "SELECT status, credential_hash IS NULL, identifier_verified_at IS NOT NULL "
                    "FROM mangaly_identity.account WHERE id = :id"
                ),
                {"id": member},
            )
        ).one()
        assert tuple(row) == ("active", True, True)
        await session.rollback()


async def test_Given_the_member_changed_identifiers_When_resolved_again_Then_row_is_synced(
    session: AsyncSession, platform_claims: Claims
) -> None:
    member = uuid.uuid4()
    new_phone = random_phone()

    async with session.begin():
        platform_claims.body = member_claims(member, random_phone(), None)
        await identity.resolve_platform_session(session, "tok")

        platform.clear_cache()
        platform_claims.body = member_claims(member, new_phone, "New.Address@Example.test")
        await identity.resolve_platform_session(session, "tok")

        assert await identity.get_own_identifiers(session, account_id=member) == (
            new_phone,
            "new.address@example.test",
        )
        await session.rollback()


async def test_Given_an_unverified_signup_holds_the_phone_When_member_enters_Then_it_retires(
    session: AsyncSession, platform_claims: Claims
) -> None:
    abandoned, member, phone = uuid.uuid4(), uuid.uuid4(), random_phone()

    async with session.begin():
        await session.execute(
            text(
                "INSERT INTO mangaly_identity.account "
                "(id, phone_identifier, credential_hash, status) "
                "VALUES (:id, :phone, 'x', 'pending_verification')"
            ),
            {"id": abandoned, "phone": phone},
        )
        platform_claims.body = member_claims(member, phone, None)

        assert (await identity.resolve_platform_session(session, "tok")).account_id == member
        holder = (
            await session.execute(
                text("SELECT id, status FROM mangaly_identity.lookup_by_identifier(:p)"),
                {"p": phone},
            )
        ).all()
        assert [(r[0], str(r[1])) for r in holder] == [(member, "active")]
        await session.rollback()


async def test_Given_an_active_account_holds_the_phone_When_another_member_enters_Then_refused(
    session: AsyncSession, platform_claims: Claims
) -> None:
    owner, member, phone = uuid.uuid4(), uuid.uuid4(), random_phone()

    async with session.begin():
        await session.execute(
            text(
                "INSERT INTO mangaly_identity.account "
                "(id, phone_identifier, credential_hash, status) "
                "VALUES (:id, :phone, 'x', 'active')"
            ),
            {"id": owner, "phone": phone},
        )
        platform_claims.body = member_claims(member, phone, None)

        with pytest.raises(identity.PlatformLinkRefused) as refused:
            await identity.resolve_platform_session(session, "tok")
        assert refused.value.code == "platform_identity_conflict"
        await session.rollback()


async def test_Given_claims_without_identifiers_When_resolved_Then_it_fails_closed(
    session: AsyncSession, platform_claims: Claims
) -> None:
    platform_claims.body = member_claims(uuid.uuid4(), None, None)

    async with session.begin():
        with pytest.raises(identity.PlatformIdentityUnavailable):
            await identity.resolve_platform_session(session, "tok")
        await session.rollback()


# --- End to end through the FastAPI dependency --------------------------------


def app_over(session: AsyncSession, settings: Settings) -> FastAPI:
    app = FastAPI()

    @app.get("/probe")
    async def probe(account_id: deps.AuthenticatedAccount) -> dict[str, str]:
        return {"account_id": str(account_id)}

    async def same_session():  # type: ignore[no-untyped-def]
        yield session

    app.dependency_overrides[deps.get_db_session] = same_session
    app.dependency_overrides[get_settings] = lambda: settings
    return app


def client_for(app: FastAPI, **kwargs: object) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://mangaly.test",
        **kwargs,  # type: ignore[arg-type]
    )


async def test_Given_an_fk_session_cookie_When_calling_the_api_Then_the_member_is_the_caller(
    session: AsyncSession, platform_claims: Claims
) -> None:
    member = uuid.uuid4()
    platform_claims.body = member_claims(member, random_phone(), None)

    async with session.begin():
        app = app_over(session, Settings(interim_identity_enabled=False))
        async with client_for(app, cookies={"fk_session": "tok"}) as client:
            response = await client.get("/probe")
        assert response.status_code == 200
        assert response.json() == {"account_id": str(member)}
        await session.rollback()


async def test_Given_a_legacy_session_When_interim_is_enabled_or_not_Then_only_enabled_accepts(
    session: AsyncSession,
) -> None:
    """TR15 step 5: the interim path still works — but only behind the flag."""
    account, legacy_session = uuid.uuid4(), uuid.uuid4()

    async with session.begin():
        await set_account_context(session, account)
        await session.execute(
            text(
                "INSERT INTO mangaly_identity.account "
                "(id, phone_identifier, credential_hash, status) "
                "VALUES (:id, :phone, 'x', 'active')"
            ),
            {"id": account, "phone": random_phone()},
        )
        await session.execute(
            text(
                "INSERT INTO mangaly_identity.session (id, account_id, expires_at) "
                "VALUES (:sid, :aid, :exp)"
            ),
            {"sid": legacy_session, "aid": account, "exp": datetime.now(UTC) + timedelta(days=1)},
        )
        headers = {"Authorization": f"Bearer {legacy_session}"}

        enabled = app_over(session, Settings(interim_identity_enabled=True))
        async with client_for(enabled) as client:
            accepted = await client.get("/probe", headers=headers)

        disabled = app_over(session, Settings(interim_identity_enabled=False))
        async with client_for(disabled) as client:
            refused = await client.get("/probe", headers=headers)

        assert accepted.status_code == 200
        assert accepted.json() == {"account_id": str(account)}
        assert refused.status_code == 401
        await session.rollback()
