"""Unit tests for the Identity Bridge's ForKhatri platform client and HTTP gating.

Per IMPLEMENTATION-TEST-STANDARDS §4 only the true external boundary is mocked:
the platform Identity & Trust Service, via `httpx.MockTransport`. Nothing here
touches the database — the HTTP-level tests prove the gate answers BEFORE any
database work, which is why they can run with no session at all.

Traces to: docs/ParentApp/07-tech-reqs.md TR14, TR15, TR16.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable, Iterator

import httpx
import pytest
from fastapi import FastAPI

from app.api import deps
from app.api.routes import auth
from app.components.identity_bridge import interface as identity_interface
from app.components.identity_bridge import platform
from app.config.settings import Settings, get_settings

Handler = Callable[[httpx.Request], httpx.Response]


def claims_body(member_id: uuid.UUID, **overrides: object) -> dict[str, object]:
    body: dict[str, object] = {
        "member_id": str(member_id),
        "display_name": "Test Member",
        "preferred_language": "en",
        "identity_level": 1,
        "status": "active",
        "session_expires_at": "2026-10-14T00:00:00+00:00",
        "phone_e164": "+919000000001",
        "email": "member@example.test",
    }
    body.update(overrides)
    return body


class FakeIdentity:
    """A scripted identity service that counts calls."""

    def __init__(self) -> None:
        self.calls: list[httpx.Request] = []
        self.handler: Handler = lambda _r: httpx.Response(500)

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.calls.append(request)
        return self.handler(request)


@pytest.fixture
def identity_service(monkeypatch: pytest.MonkeyPatch) -> Iterator[FakeIdentity]:
    fake = FakeIdentity()
    client = httpx.AsyncClient(
        transport=httpx.MockTransport(fake), base_url="http://identity.test"
    )
    monkeypatch.setattr(platform, "_client", client)
    platform.clear_cache()
    yield fake
    platform.clear_cache()


@pytest.fixture
def clock(monkeypatch: pytest.MonkeyPatch) -> Iterator[list[float]]:
    now = [1000.0]
    monkeypatch.setattr(platform, "_clock", lambda: now[0])
    yield now


# --- Resolution and cache (TR15 step 2) ---------------------------------------


async def test_Given_a_valid_token_When_resolved_twice_Then_the_service_is_called_once(
    identity_service: FakeIdentity, clock: list[float]
) -> None:
    member = uuid.uuid4()
    identity_service.handler = lambda _r: httpx.Response(200, json=claims_body(member))

    first = await platform.resolve_token("token-a")
    second = await platform.resolve_token("token-a")

    assert first == second
    assert first.member_id == member
    assert first.phone_e164 == "+919000000001"
    assert first.session_expires_at is not None
    assert first.session_expires_at.isoformat() == "2026-10-14T00:00:00+00:00"
    assert len(identity_service.calls) == 1


async def test_Given_a_cached_positive_When_30_seconds_pass_Then_it_is_resolved_again(
    identity_service: FakeIdentity, clock: list[float]
) -> None:
    identity_service.handler = lambda _r: httpx.Response(200, json=claims_body(uuid.uuid4()))

    await platform.resolve_token("token-b")
    clock[0] += platform.POSITIVE_TTL_SECONDS - 0.1
    await platform.resolve_token("token-b")
    assert len(identity_service.calls) == 1

    clock[0] += 0.2
    await platform.resolve_token("token-b")
    assert len(identity_service.calls) == 2


async def test_Given_a_revoked_token_When_resolved_Then_invalid_is_cached_for_5_seconds(
    identity_service: FakeIdentity, clock: list[float]
) -> None:
    identity_service.handler = lambda _r: httpx.Response(
        401, json={"detail": {"code": "session_invalid", "message": "x"}}
    )

    for _ in range(2):
        with pytest.raises(platform.PlatformSessionInvalid):
            await platform.resolve_token("token-c")
    assert len(identity_service.calls) == 1

    clock[0] += platform.NEGATIVE_TTL_SECONDS + 0.1
    with pytest.raises(platform.PlatformSessionInvalid):
        await platform.resolve_token("token-c")
    assert len(identity_service.calls) == 2


async def test_Given_the_cache_When_inspected_Then_it_holds_no_raw_token(
    identity_service: FakeIdentity, clock: list[float]
) -> None:
    identity_service.handler = lambda _r: httpx.Response(200, json=claims_body(uuid.uuid4()))
    await platform.resolve_token("super-secret-token")

    assert "super-secret-token" not in platform._cache
    assert platform.token_digest("super-secret-token") in platform._cache


async def test_Given_a_resolve_call_When_sent_Then_it_carries_only_the_token(
    identity_service: FakeIdentity, clock: list[float]
) -> None:
    identity_service.handler = lambda _r: httpx.Response(200, json=claims_body(uuid.uuid4()))
    await platform.resolve_token("token-d")

    request = identity_service.calls[0]
    assert request.url.path == "/internal/v1/sessions/resolve"
    assert request.method == "POST"
    assert request.read() == b'{"session_token":"token-d"}'


async def test_Given_settings_When_the_real_client_is_built_Then_service_headers_are_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(platform, "_client", None)
    client = platform._get_client()
    try:
        settings = get_settings()
        assert client.headers["X-ForKhatri-Service"] == settings.platform_service_name
        assert client.headers["X-ForKhatri-Service-Key"] == settings.platform_service_key
        assert client.timeout.read == settings.platform_identity_timeout_seconds
    finally:
        await platform.aclose_client()


# --- Fail closed (TR15 step 3) ------------------------------------------------


async def test_Given_the_service_is_unreachable_When_resolving_Then_unavailable_and_not_cached(
    identity_service: FakeIdentity, clock: list[float]
) -> None:
    def refuse(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    identity_service.handler = refuse

    for _ in range(2):
        with pytest.raises(platform.PlatformIdentityUnavailable):
            await platform.resolve_token("token-e")
    assert len(identity_service.calls) == 2


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(500),
        httpx.Response(401, json={"detail": {"code": "service_unauthorized", "message": "x"}}),
        httpx.Response(200, json={"unexpected": True}),
    ],
    ids=["server-error", "our-service-key-rejected", "malformed-claims"],
)
async def test_Given_an_unusable_answer_When_resolving_Then_it_is_unavailable_not_signed_out(
    identity_service: FakeIdentity, clock: list[float], response: httpx.Response
) -> None:
    identity_service.handler = lambda _r: response

    with pytest.raises(platform.PlatformIdentityUnavailable):
        await platform.resolve_token("token-f")


async def test_Given_an_empty_or_oversized_token_When_resolving_Then_no_call_is_made(
    identity_service: FakeIdentity,
) -> None:
    for token in ("", "x" * 129):
        with pytest.raises(platform.PlatformSessionInvalid):
            await platform.resolve_token(token)
    assert identity_service.calls == []


# --- HTTP gating (TR15 step 3/5, TR16) ----------------------------------------


def make_app(settings: Settings) -> FastAPI:
    app = FastAPI()
    app.include_router(auth.router)

    @app.get("/probe")
    async def probe(account_id: deps.AuthenticatedAccount) -> dict[str, str]:
        return {"account_id": str(account_id)}

    async def no_database():  # type: ignore[no-untyped-def]
        # Any handler that reached the database would fail on None — so a
        # clean 401/410/503 proves the gate answered first.
        yield None

    app.dependency_overrides[deps.get_db_session] = no_database
    app.dependency_overrides[get_settings] = lambda: settings
    return app


def http_client(app: FastAPI, cookies: dict[str, str] | None = None) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://mangaly.test", cookies=cookies
    )


async def test_Given_identity_is_down_When_a_member_calls_the_api_Then_503_never_a_default(
    identity_service: FakeIdentity,
) -> None:
    def refuse(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("timed out", request=request)

    identity_service.handler = refuse
    settings = Settings(interim_identity_enabled=False)

    async with http_client(make_app(settings), {"fk_session": "tok"}) as client:
        response = await client.get("/probe")

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "identity_unavailable"


async def test_Given_a_revoked_platform_session_When_calling_the_api_Then_401(
    identity_service: FakeIdentity,
) -> None:
    identity_service.handler = lambda _r: httpx.Response(
        401, json={"detail": {"code": "session_invalid", "message": "x"}}
    )
    settings = Settings(interim_identity_enabled=False)

    async with http_client(make_app(settings), {"fk_session": "tok"}) as client:
        response = await client.get("/probe")

    assert response.status_code == 401


async def test_Given_interim_disabled_When_a_legacy_credential_is_sent_Then_it_is_ignored(
    identity_service: FakeIdentity,
) -> None:
    settings = Settings(interim_identity_enabled=False)
    legacy = str(uuid.uuid4())

    async with http_client(make_app(settings), {"mangaly_session": legacy}) as client:
        by_cookie = await client.get("/probe")
        by_bearer = await client.get("/probe", headers={"Authorization": f"Bearer {legacy}"})

    assert by_cookie.status_code == 401
    assert by_bearer.status_code == 401
    assert identity_service.calls == []


@pytest.mark.parametrize(
    "path",
    [
        "/auth/signup",
        "/auth/login",
        "/auth/login/otp/request",
        "/auth/otp/verify",
        "/auth/otp/resend",
        "/auth/reset/request",
        "/auth/reset/confirm",
    ],
)
async def test_Given_interim_disabled_When_a_credential_route_is_called_Then_410_moved(
    path: str,
) -> None:
    settings = Settings(interim_identity_enabled=False, forkhatri_entrance_url="http://hub.test")

    async with http_client(make_app(settings)) as client:
        response = await client.post(path, json={})

    assert response.status_code == 410
    detail = response.json()["detail"]
    assert detail["code"] == "moved_to_forkhatri"
    assert detail["entrance_url"] == "http://hub.test"
    assert detail["message"]


async def test_Given_a_platform_session_When_auth_me_is_called_Then_expires_at_is_the_claims_expiry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`/auth/me` returns the platform `session_expires_at` (ISO 8601), not ""."""
    from datetime import datetime

    member = uuid.uuid4()
    expiry = datetime.fromisoformat("2026-10-14T12:53:02.944445+00:00")
    seen: list[str] = []

    async def fake_resolve(_session: object, token: str) -> identity_interface.PlatformSession:
        seen.append(token)
        return identity_interface.PlatformSession(account_id=member, expires_at=expiry)

    monkeypatch.setattr(identity_interface, "resolve_platform_session", fake_resolve)
    settings = Settings(interim_identity_enabled=False)

    async with http_client(make_app(settings), {"fk_session": "tok"}) as client:
        response = await client.get("/auth/me")

    assert response.status_code == 200
    assert response.json() == {
        "account_id": str(member),
        "expires_at": "2026-10-14T12:53:02.944445+00:00",
    }
    assert seen == ["tok"]


async def test_Given_claims_with_a_bad_expiry_When_resolving_Then_it_is_unavailable(
    identity_service: FakeIdentity, clock: list[float]
) -> None:
    identity_service.handler = lambda _r: httpx.Response(
        200, json=claims_body(uuid.uuid4(), session_expires_at="not-a-date")
    )

    with pytest.raises(platform.PlatformIdentityUnavailable):
        await platform.resolve_token("token-g")
