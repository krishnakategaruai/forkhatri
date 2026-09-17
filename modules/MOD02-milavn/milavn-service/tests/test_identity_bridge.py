"""Identity Bridge against the ForKhatri platform contract (ParentApp 07-tech-reqs TR14/TR15).

No network and no database: the platform is an `httpx.MockTransport`, and the
request-layer tests use a stand-in session that records the RLS binding.
"""

from __future__ import annotations

import hashlib
import json
from uuid import UUID

import httpx
import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.api import deps
from app.components.identity_bridge import interface as bridge
from app.config.settings import get_settings

ASHA = UUID("11111111-1111-1111-1111-111111111111")
MODERATOR = UUID("99999999-9999-9999-9999-999999999999")
NEWCOMER = UUID("a0000000-0000-4000-8000-000000000001")
UNKNOWN = UUID("12345678-1234-1234-1234-123456789012")


class Platform:
    """Scripted Identity & Trust Service; counts calls per path."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []
        self.sessions: dict[str, dict] = {}
        self.members: dict[str, dict] = {}
        self.down = False
        self.resolve_status: int | None = None

    def handler(self, request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content or b"{}")
        self.calls.append((request.url.path, body))
        if self.down:
            raise httpx.ConnectError("refused", request=request)
        assert request.headers["X-ForKhatri-Service"] == "milavn"
        if request.url.path == "/internal/v1/sessions/resolve":
            if self.resolve_status:
                return httpx.Response(self.resolve_status, json={"detail": {"code": "x"}})
            claims = self.sessions.get(body["session_token"])
            if claims is None:
                return httpx.Response(401, json={"detail": {"code": "session_invalid", "message": "The session is not valid."}})
            return httpx.Response(200, json=claims)
        if request.url.path == "/internal/v1/members/lookup":
            assert len(body["member_ids"]) <= bridge.LOOKUP_BATCH_MAX
            return httpx.Response(200, json=[self.members[i] for i in body["member_ids"] if i in self.members])
        return httpx.Response(404)

    def count(self, path: str) -> int:
        return sum(1 for p, _ in self.calls if p == path)


@pytest.fixture
async def platform(monkeypatch):
    p = Platform()
    await bridge.aclose()
    bridge.reset_caches()
    monkeypatch.setattr(bridge, "_transport_factory", lambda: httpx.MockTransport(p.handler))
    p.sessions["tok-asha"] = {
        "member_id": str(ASHA),
        "display_name": "Asha Reddy",
        "preferred_language": "en",
        "identity_level": 2,
        "status": "active",
        "session_expires_at": "2099-01-01T00:00:00+00:00",
    }
    p.sessions["tok-mod"] = {**p.sessions["tok-asha"], "member_id": str(MODERATOR), "display_name": "Milavn Moderator"}
    p.sessions["tok-new"] = {**p.sessions["tok-asha"], "member_id": str(NEWCOMER), "display_name": "Krishna Kategaru", "identity_level": 1}
    p.members[str(ASHA)] = {"member_id": str(ASHA), "display_name": "Asha Reddy", "identity_level": 2}
    p.members[str(NEWCOMER)] = {"member_id": str(NEWCOMER), "display_name": "Krishna Kategaru", "identity_level": 1}
    yield p
    await bridge.aclose()
    bridge.reset_caches()


RESOLVE = "/internal/v1/sessions/resolve"
LOOKUP = "/internal/v1/members/lookup"


async def test_Given_valid_session_When_resolved_twice_Then_platform_called_once(platform):
    first = await bridge.resolve_session("tok-asha")
    second = await bridge.resolve_session("tok-asha")
    assert first == second and first is not None
    assert first.member_id == ASHA and first.display_name == "Asha Reddy" and first.identity_level == 2
    assert platform.count(RESOLVE) == 1
    # The cache is keyed by the token's digest, never the token itself.
    assert "tok-asha" not in bridge._sessions
    assert hashlib.sha256(b"tok-asha").hexdigest() in bridge._sessions


async def test_Given_positive_cache_expired_When_resolved_Then_platform_asked_again(platform):
    await bridge.resolve_session("tok-asha")
    key = hashlib.sha256(b"tok-asha").hexdigest()
    bridge._sessions[key] = (0.0, bridge._sessions[key][1])  # 30 s elapsed
    del platform.sessions["tok-asha"]  # signed out on the platform meanwhile
    assert await bridge.resolve_session("tok-asha") is None
    assert platform.count(RESOLVE) == 2


async def test_Given_invalid_session_When_resolved_Then_none_and_negative_cache_is_short(platform):
    assert await bridge.resolve_session("bogus") is None
    assert await bridge.resolve_session("bogus") is None
    assert platform.count(RESOLVE) == 1
    expires, value = bridge._sessions[hashlib.sha256(b"bogus").hexdigest()]
    assert value is None
    import time

    assert expires - time.monotonic() <= bridge.NEGATIVE_SESSION_TTL_SECONDS


async def test_Given_platform_unreachable_When_resolving_Then_raises_and_nothing_cached(platform):
    platform.down = True
    with pytest.raises(bridge.IdentityServiceUnavailable):
        await bridge.resolve_session("tok-asha")
    assert bridge._sessions == {}
    platform.down = False
    assert (await bridge.resolve_session("tok-asha")).member_id == ASHA


async def test_Given_service_key_refused_When_resolving_Then_unavailable_not_signed_out(platform):
    platform.resolve_status = 403
    with pytest.raises(bridge.IdentityServiceUnavailable):
        await bridge.resolve_session("tok-asha")
    assert bridge._sessions == {}


async def test_Given_moderator_When_resolved_Then_scope_comes_from_milavn_role_source(platform):
    mod = await bridge.resolve_session("tok-mod")
    assert mod.is_moderator and mod.scopes == ("milavn.moderate",)
    newcomer = await bridge.resolve_session("tok-new")
    assert newcomer.scopes == () and newcomer.avatar is None and newcomer.handle == "krishna.kategaru"


async def test_Given_known_and_unknown_ids_When_display_names_Then_fallback_and_cached(platform):
    names = await bridge.display_names_for([ASHA, UNKNOWN, ASHA])
    assert names[ASHA].display_name == "Asha Reddy"
    assert names[UNKNOWN].display_name == bridge.FALLBACK_DISPLAY_NAME
    await bridge.display_names_for([ASHA, UNKNOWN])
    assert platform.count(LOOKUP) == 1


async def test_Given_platform_down_When_display_names_Then_fallback_without_raising(platform):
    platform.down = True
    names = await bridge.display_names_for([ASHA])
    assert names[ASHA].display_name == bridge.FALLBACK_DISPLAY_NAME
    # Backoff: a burst of lookups during an outage does not re-dial the platform.
    await bridge.display_names_for([NEWCOMER])
    assert platform.count(LOOKUP) == 1
    assert ASHA not in bridge._names  # the fallback is not cached as the real name


async def test_Given_more_than_200_ids_When_display_names_Then_batched(platform):
    ids = [UUID(int=i + 1) for i in range(450)]
    names = await bridge.display_names_for(ids)
    assert len(names) == 450 and platform.count(LOOKUP) == 3


# --- request layer (deps.py) ----------------------------------------------------------


class FakeSession:
    def __init__(self) -> None:
        self.bound: list[dict] = []

    def in_transaction(self) -> bool:
        return True

    async def execute(self, _stmt, params=None):  # noqa: ANN001, ANN202
        self.bound.append(params)


def _request(method: str = "GET", cookies: str | None = None, headers: dict[str, str] | None = None) -> Request:
    raw = [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()]
    if cookies:
        raw.append((b"cookie", cookies.encode()))
    return Request({"type": "http", "method": method, "path": "/identity/me", "headers": raw, "query_string": b""})


@pytest.fixture
def dev_flag(monkeypatch):
    settings = get_settings()

    def set_flag(on: bool) -> None:
        monkeypatch.setattr(settings, "dev_identity_enabled", on)

    set_flag(False)
    return set_flag


async def test_Given_fk_session_cookie_When_request_Then_member_bound_for_rls(platform, dev_flag):
    s = FakeSession()
    member = await deps.get_optional_member(_request(cookies="fk_session=tok-asha"), s, None)
    assert member.member_id == ASHA and member.identity_level == 2
    assert {"name": "milavn.member_id", "value": str(ASHA)} in s.bound


async def test_Given_platform_down_When_authenticated_request_Then_503(platform, dev_flag):
    platform.down = True
    with pytest.raises(HTTPException) as exc:
        await deps.get_optional_member(_request(cookies="fk_session=tok-asha"), FakeSession(), None)
    assert exc.value.status_code == 503


async def test_Given_no_cookie_When_request_Then_anonymous_without_calling_platform(platform, dev_flag):
    s = FakeSession()
    assert await deps.get_optional_member(_request(), s, None) is None
    assert {"name": "milavn.member_id", "value": str(deps.ANONYMOUS_MEMBER_ID)} in s.bound
    assert platform.calls == []


async def test_Given_dev_flag_off_When_only_member_header_Then_anonymous(platform, dev_flag):
    assert await deps.get_optional_member(_request(), FakeSession(), str(ASHA)) is None
    assert bridge.list_dev_members() == []


async def test_Given_dev_flag_on_When_member_header_Then_legacy_identity(platform, dev_flag):
    dev_flag(True)
    member = await deps.get_optional_member(_request(), FakeSession(), str(ASHA))
    assert member.member_id == ASHA and member.handle == "asha"


async def test_Given_cookie_session_When_cross_origin_post_Then_403(platform, dev_flag):
    req = _request("POST", cookies="fk_session=tok-asha", headers={"Origin": "http://evil.example"})
    with pytest.raises(HTTPException) as exc:
        await deps.get_optional_member(req, FakeSession(), None)
    assert exc.value.status_code == 403
    ok = _request("POST", cookies="fk_session=tok-asha", headers={"Origin": "http://localhost:3001"})
    assert (await deps.get_optional_member(ok, FakeSession(), None)).member_id == ASHA
