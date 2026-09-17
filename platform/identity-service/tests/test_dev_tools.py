"""Development member switcher (07-tech-reqs.md "Development tools").

Proves: the router is absent unless development + DEV_TOOLS_ENABLED (and not the
LOCAL_HTTP_TEST rehearsal); production refuses DEV_TOOLS_ENABLED=true; the session
token never appears in a response body without the dev token header. No database
is needed: the database dependency and the session-opening function are replaced.
"""

from __future__ import annotations

import importlib.util
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.api.deps import get_db
from app.components.identity import interface as identity
from app.config.settings import Settings, get_settings
from app.dev_tools.personas import NEW_MEMBER_ID, OWNER_MEMBER_ID, PERSONAS
from app.main import create_app

TOKEN = "dev-token-for-unit-tests-0123456789abcdef"
SESSION_TOKEN = "session-token-that-must-never-leak-in-a-body"
ASHA = UUID("11111111-1111-1111-1111-111111111111")

PRODUCTION_READY = {
    "environment": "production",
    "session_cookie_secure": True,
    "session_cookie_name": "__Host-fk_session",
    "dev_expose_otp": False,
    "otp_pepper": "p" * 40,
    "service_keys": {"mangaly": "m" * 40, "milavn": "v" * 40},
    "sms_provider": "disabled",
    "email_provider": "disabled",
}


def settings(**overrides: object) -> Settings:
    return Settings(_env_file=None, **overrides)  # type: ignore[call-arg]


def dev_settings(**overrides: object) -> Settings:
    return settings(**{"environment": "development", "dev_tools_enabled": True, "dev_tools_token": TOKEN, **overrides})


class FakeDb:
    async def commit(self) -> None:
        return None


def client_for(config: Settings, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    app = create_app(config)

    async def fake_db() -> AsyncIterator[FakeDb]:
        yield FakeDb()

    async def fake_open(_db: object, _settings: Settings, member_id: UUID, _ua: str | None) -> identity.SignedIn:
        member = identity.Member(member_id, "Asha Reddy", "en", 1, "active", "+919800000001", None)
        return identity.SignedIn(member, SESSION_TOKEN, datetime.now(UTC) + timedelta(days=30))

    app.dependency_overrides[get_settings] = lambda: config
    app.dependency_overrides[get_db] = fake_db
    monkeypatch.setattr(identity, "open_development_session", fake_open)
    return TestClient(app)


def dev_paths(config: Settings) -> list[str]:
    return [path for path in create_app(config).openapi()["paths"] if path.startswith("/dev")]


@pytest.mark.parametrize(
    "config",
    [
        settings(),
        settings(environment="development", dev_tools_enabled=False, dev_tools_token=TOKEN),
        dev_settings(local_http_test=True),
    ],
    ids=["default", "flag-off", "local-http-rehearsal"],
)
def test_router_is_absent_unless_enabled_in_development(config: Settings) -> None:
    assert dev_paths(config) == []
    client = TestClient(create_app(config))
    assert client.post("/dev/v1/sessions", json={"persona": "asha"}).status_code == 404
    assert client.get("/dev/v1/personas").status_code == 404


def test_router_is_mounted_when_enabled_in_development() -> None:
    assert sorted(dev_paths(dev_settings())) == ["/dev/v1/personas", "/dev/v1/sessions"]


def test_production_refuses_dev_tools() -> None:
    assert settings(**PRODUCTION_READY).dev_tools_active is False
    for extra in ({"dev_tools_enabled": True}, {"dev_tools_enabled": True, "local_http_test": True}):
        with pytest.raises(ValidationError, match="DEV_TOOLS_ENABLED must be false"):
            settings(**{**PRODUCTION_READY, **extra})


def test_browser_mode_sets_the_cookie_and_never_returns_the_token(monkeypatch: pytest.MonkeyPatch) -> None:
    response = client_for(dev_settings(), monkeypatch).post("/dev/v1/sessions", json={"persona": "asha"})
    assert response.status_code == 200, response.text
    assert response.json()["outcome"] == "signed_in"
    assert "session_token" not in response.json()
    assert SESSION_TOKEN not in response.text
    cookie = response.headers["set-cookie"].lower()
    assert SESSION_TOKEN in response.headers["set-cookie"] and "httponly" in cookie and "samesite=lax" in cookie
    assert response.headers["cache-control"] == "no-store"


def test_test_mode_returns_the_token_only_with_the_right_header(monkeypatch: pytest.MonkeyPatch) -> None:
    client = client_for(dev_settings(), monkeypatch)
    ok = client.post("/dev/v1/sessions", json={"member_id": str(ASHA)}, headers={"X-ForKhatri-Dev-Token": TOKEN})
    assert ok.status_code == 200 and ok.json()["session_token"] == SESSION_TOKEN
    assert "set-cookie" not in ok.headers

    for presented in ("wrong", ""):
        refused = client.post("/dev/v1/sessions", json={"persona": "asha"}, headers={"X-ForKhatri-Dev-Token": presented})
        assert refused.status_code == 403 and refused.json()["detail"]["code"] == "dev_token_invalid"
        assert SESSION_TOKEN not in refused.text


def test_test_mode_needs_a_configured_token(monkeypatch: pytest.MonkeyPatch) -> None:
    client = client_for(dev_settings(dev_tools_token="short"), monkeypatch)
    response = client.post("/dev/v1/sessions", json={"persona": "asha"}, headers={"X-ForKhatri-Dev-Token": "short"})
    assert response.status_code == 403 and SESSION_TOKEN not in response.text


def test_tests_can_never_act_as_the_owner(monkeypatch: pytest.MonkeyPatch) -> None:
    client = client_for(dev_settings(), monkeypatch)
    for body in ({"persona": "krishna"}, {"member_id": str(OWNER_MEMBER_ID)}):
        response = client.post("/dev/v1/sessions", json=body, headers={"X-ForKhatri-Dev-Token": TOKEN})
        assert response.status_code == 403 and response.json()["detail"]["code"] == "owner_reserved"


def test_request_validation_and_origin_guard(monkeypatch: pytest.MonkeyPatch) -> None:
    client = client_for(dev_settings(), monkeypatch)
    assert client.post("/dev/v1/sessions", json={}).status_code == 422
    assert client.post("/dev/v1/sessions", json={"persona": "asha", "member_id": str(ASHA)}).status_code == 422
    unknown = client.post("/dev/v1/sessions", json={"persona": "nobody"})
    assert unknown.status_code == 404 and unknown.json()["detail"]["code"] == "persona_unknown"
    foreign = client.post("/dev/v1/sessions", json={"persona": "asha"}, headers={"Origin": "https://evil.example"})
    assert foreign.status_code == 403 and foreign.json()["detail"]["code"] == "origin_not_allowed"


def test_seeded_members_match_the_personas() -> None:
    path = Path(__file__).resolve().parents[1] / "scripts" / "seed_dev_members.py"
    spec = importlib.util.spec_from_file_location("seed_dev_members", path)
    assert spec and spec.loader
    seed = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(seed)
    seeded = {member["id"] for member in seed.NEW_MEMBERS}
    assert {OWNER_MEMBER_ID, NEW_MEMBER_ID} <= seeded
    assert seeded <= {persona.member_id for persona in PERSONAS}, "every seeded development member needs a persona"
    assert [p.key for p in PERSONAS if not p.for_automated_tests] == ["krishna"]


def test_opening_a_dev_session_refuses_when_tools_are_inactive() -> None:
    import asyncio

    with pytest.raises(RuntimeError):
        asyncio.run(identity.open_development_session(FakeDb(), settings(), ASHA, None))  # type: ignore[arg-type]
