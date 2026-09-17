"""Live contract checks against a running Identity & Trust Service (07-tech-reqs.md TR12-TR20).

Skipped unless IDENTITY_LIVE_URL is set:
    $env:IDENTITY_LIVE_URL = "http://localhost:8100"
Requires the development seed (scripts/seed_dev_members.py) and DEV_EXPOSE_OTP=true.
"""

from __future__ import annotations

import os
import secrets
from collections.abc import Iterator
from uuid import uuid4

import httpx
import pytest

BASE_URL = os.environ.get("IDENTITY_LIVE_URL")
pytestmark = pytest.mark.skipif(not BASE_URL, reason="IDENTITY_LIVE_URL is not set")
# Behind the deployment edge (e.g. http://localhost:8080/api/identity) the public API
# lives under a prefix, the allowed Origin is the public origin, and /internal is not
# reachable, so internal calls go straight to the service.
ORIGIN = os.environ.get("IDENTITY_LIVE_ORIGIN", "http://localhost:3100")
INTERNAL_URL = os.environ.get("IDENTITY_LIVE_INTERNAL_URL") or BASE_URL or ""

DEV_PASSWORD = "ForKhatri-dev-2026"
KRISHNA = {"id": "a0000000-0000-4000-8000-000000000001", "phone": "+919999900001"}
ASHA_PHONE = "+919800000001"


def service_headers(name: str) -> dict[str, str]:
    return {
        "X-ForKhatri-Service": name,
        "X-ForKhatri-Service-Key": os.environ.get(f"{name.upper()}_SERVICE_KEY", f"CHANGE_ME_dev_{name}_service_key"),
    }


def internal_post(path: str, **kwargs: object) -> httpx.Response:
    return httpx.post(f"{INTERNAL_URL}{path}", timeout=15, **kwargs)  # type: ignore[arg-type]


@pytest.fixture
def client() -> Iterator[httpx.Client]:
    with httpx.Client(base_url=BASE_URL or "", headers={"Origin": ORIGIN}, timeout=15) as c:
        yield c


def fresh_mobile() -> str:
    return "7" + "".join(secrets.choice("0123456789") for _ in range(9))


def error_code(response: httpx.Response) -> str:
    return response.json()["detail"]["code"]


def session_header(response: httpx.Response, client: httpx.Client) -> dict[str, str]:
    token = response.cookies.get("fk_session")
    assert token, "sign-in must set the fk_session cookie"
    client.cookies.clear()
    return {"Cookie": f"fk_session={token}"}


def password_sign_in(client: httpx.Client, identifier: str) -> tuple[httpx.Response, dict[str, str]]:
    response = client.post("/v1/auth/password", json={"identifier": identifier, "password": DEV_PASSWORD})
    assert response.status_code == 200, response.text
    return response, session_header(response, client)


def test_health(client: httpx.Client) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "identity"}


def test_registry_is_readable_signed_out(client: httpx.Client) -> None:
    modules = client.get("/v1/modules").json()
    by_key = {m["key"]: m for m in modules}
    assert [m["key"] for m in modules][:2] == ["mangaly", "milavn"]
    assert by_key["mangaly"]["availability"] == "available" and by_key["mangaly"]["entry_url"]
    assert by_key["vyapar"]["availability"] == "in_development" and by_key["vyapar"]["entry_url"] is None
    assert all(m["last_entered_at"] is None for m in modules)


def test_new_member_code_flow_entry_and_sign_out(client: httpx.Client) -> None:
    mobile = fresh_mobile()
    started = client.post("/v1/auth/code", json={"identifier": mobile})
    assert started.status_code == 202
    challenge = started.json()
    assert challenge["channel"] == "sms"
    assert challenge["destination_hint"].endswith(mobile[-4:]) and mobile not in started.text
    assert len(challenge["dev_code"]) == 6

    verified = client.post(
        "/v1/auth/code/verify", json={"challenge_id": challenge["challenge_id"], "code": challenge["dev_code"]}
    )
    assert verified.json() == {"outcome": "name_required"}
    assert "fk_session" not in verified.cookies

    welcome_body = {
        "challenge_id": challenge["challenge_id"],
        "code": challenge["dev_code"],
        "display_name": "  Live Test Member  ",
        "preferred_language": "hi",
    }
    welcomed = client.post("/v1/auth/welcome", json=welcome_body)
    assert welcomed.status_code == 201, welcomed.text
    set_cookie = welcomed.headers["set-cookie"].lower()
    assert "httponly" in set_cookie and "samesite=lax" in set_cookie and "path=/" in set_cookie
    member = welcomed.json()["member"]
    assert member["display_name"] == "Live Test Member"
    assert member["phone_hint"].endswith(mobile[-4:]) and mobile not in welcomed.text
    cookie = session_header(welcomed, client)

    assert client.get("/v1/session", headers=cookie).status_code == 200
    taglines = client.get("/v1/modules", headers=cookie).json()
    assert any("ऀ" <= ch <= "ॿ" for ch in taglines[0]["tagline"]), "member language drives taglines"

    entered = client.post("/v1/modules/milavn/enter", headers=cookie)
    assert entered.status_code == 200 and entered.json()["entry_url"].startswith("http")
    ordered = {m["key"]: m for m in client.get("/v1/modules", headers=cookie).json()}
    assert ordered["milavn"]["last_entered_at"] is not None

    unavailable = client.post("/v1/modules/vyapar/enter", headers=cookie)
    assert unavailable.status_code == 409 and error_code(unavailable) == "module_unavailable"
    assert client.post("/v1/modules/unknown/enter", headers=cookie).status_code == 404

    patched = client.patch("/v1/me", json={"preferred_language": "te"}, headers=cookie)
    assert patched.status_code == 200 and patched.json()["preferred_language"] == "te"
    assert "home_locality" not in patched.json(), "the platform holds basic identity only"
    profile_field = client.patch("/v1/me", json={"home_locality": "Kukatpally"}, headers=cookie)
    assert profile_field.status_code == 422, "profile details belong to modules, not the platform"
    assert client.patch("/v1/me", json={"display_name": "  "}, headers=cookie).status_code == 422

    signed_out = client.post("/v1/auth/sign-out", json={"everywhere": False}, headers=cookie)
    assert signed_out.status_code == 204
    after = client.get("/v1/session", headers=cookie)
    assert after.status_code == 401 and error_code(after) == "not_signed_in"

    replay = client.post("/v1/auth/welcome", json=welcome_body)
    assert replay.status_code == 400 and error_code(replay) == "code_invalid"


def test_password_failures_are_indistinguishable(client: httpx.Client) -> None:
    password_sign_in(client, ASHA_PHONE)
    wrong = client.post("/v1/auth/password", json={"identifier": ASHA_PHONE, "password": "not-it"})
    unknown = client.post("/v1/auth/password", json={"identifier": "+917000000999", "password": "not-it"})
    malformed = client.post("/v1/auth/password", json={"identifier": "nobody", "password": "not-it"})
    for response in (wrong, unknown, malformed):
        assert response.status_code == 401
        assert response.json() == wrong.json()


def test_internal_resolve_minimises_identifiers(client: httpx.Client) -> None:
    _, cookie = password_sign_in(client, KRISHNA["phone"])
    token = cookie["Cookie"].split("=", 1)[1]

    for_milavn = internal_post("/internal/v1/sessions/resolve", json={"session_token": token}, headers=service_headers("milavn"))
    assert for_milavn.status_code == 200
    assert for_milavn.json()["member_id"] == KRISHNA["id"]
    assert "phone_e164" not in for_milavn.json() and "email" not in for_milavn.json()

    for_mangaly = internal_post("/internal/v1/sessions/resolve", json={"session_token": token}, headers=service_headers("mangaly"))
    assert for_mangaly.json()["phone_e164"] == KRISHNA["phone"]

    bad_key = internal_post(
        "/internal/v1/sessions/resolve",
        json={"session_token": token},
        headers={"X-ForKhatri-Service": "milavn", "X-ForKhatri-Service-Key": "wrong"},
    )
    assert bad_key.status_code == 401 and error_code(bad_key) == "service_unauthorized"

    invalid = internal_post("/internal/v1/sessions/resolve", json={"session_token": "nope"}, headers=service_headers("milavn"))
    assert invalid.status_code == 401 and error_code(invalid) == "session_invalid"

    lookup = internal_post(
        "/internal/v1/members/lookup",
        json={"member_ids": [KRISHNA["id"], str(uuid4())]},
        headers=service_headers("milavn"),
    )
    assert lookup.status_code == 200
    assert lookup.json() == [{"member_id": KRISHNA["id"], "display_name": "Krishna Kategaru", "identity_level": 1}]


def test_foreign_origin_cannot_change_state(client: httpx.Client) -> None:
    response = client.post(
        "/v1/auth/password",
        json={"identifier": ASHA_PHONE, "password": DEV_PASSWORD},
        headers={"Origin": "https://evil.example"},
    )
    assert response.status_code == 403 and error_code(response) == "origin_not_allowed"


def test_resend_interval_is_enforced(client: httpx.Client) -> None:
    mobile = fresh_mobile()
    assert client.post("/v1/auth/code", json={"identifier": mobile}).status_code == 202
    again = client.post("/v1/auth/code", json={"identifier": mobile})
    assert again.status_code == 429 and error_code(again) == "rate_limited"
    assert int(again.headers["Retry-After"]) >= 1


def test_wrong_codes_exhaust_the_challenge(client: httpx.Client) -> None:
    challenge = client.post("/v1/auth/code", json={"identifier": fresh_mobile()}).json()
    wrong = f"{(int(challenge['dev_code']) + 1) % 1_000_000:06d}"
    codes = [
        error_code(client.post("/v1/auth/code/verify", json={"challenge_id": challenge["challenge_id"], "code": wrong}))
        for _ in range(5)
    ]
    assert codes == ["code_invalid"] * 4 + ["code_attempts_exhausted"]
    correct = client.post(
        "/v1/auth/code/verify", json={"challenge_id": challenge["challenge_id"], "code": challenge["dev_code"]}
    )
    assert error_code(correct) == "code_attempts_exhausted"


def _dev_tools_token() -> str:
    if os.environ.get("DEV_TOOLS_TOKEN"):
        return os.environ["DEV_TOOLS_TOKEN"]
    from app.config.settings import get_settings

    return get_settings().dev_tools_token


def test_dev_tools_switch_members(client: httpx.Client) -> None:
    """Development tools only ("Development tools" in 07-tech-reqs.md); skipped when not mounted."""
    listed = client.get("/dev/v1/personas")
    if listed.status_code == 404:
        pytest.skip("development tools are not mounted on this service")
    personas = {p["key"]: p for p in listed.json()}
    assert {"krishna", "asha", "new-member", "mangaly-family", "milavn-moderator"} <= set(personas)
    assert personas["krishna"]["for_automated_tests"] is False and personas["krishna"]["member_id"] == KRISHNA["id"]
    assert listed.headers["cache-control"] == "no-store"

    first = client.post("/dev/v1/sessions", json={"persona": "new-member"})
    assert first.status_code == 200, first.text
    assert "session_token" not in first.json() and first.json()["member"]["member_id"] == personas["new-member"]["member_id"]
    assert "httponly" in first.headers["set-cookie"].lower()
    first_cookie = session_header(first, client)
    assert client.get("/v1/session", headers=first_cookie).json()["member"]["display_name"] == "New Member"

    # Switching from a signed-in browser replaces that browser's session (never "everywhere").
    second = client.post("/dev/v1/sessions", json={"persona": "asha"}, headers=first_cookie)
    second_cookie = session_header(second, client)
    assert client.get("/v1/session", headers=first_cookie).status_code == 401
    assert client.get("/v1/session", headers=second_cookie).json()["member"]["member_id"] == personas["asha"]["member_id"]
    resolved = internal_post(
        "/internal/v1/sessions/resolve",
        json={"session_token": second_cookie["Cookie"].split("=", 1)[1]},
        headers=service_headers("milavn"),
    )
    assert resolved.status_code == 200 and resolved.json()["member_id"] == personas["asha"]["member_id"]

    foreign = client.post("/dev/v1/sessions", json={"persona": "asha"}, headers={"Origin": "https://evil.example"})
    assert foreign.status_code == 403 and error_code(foreign) == "origin_not_allowed"
    wrong = client.post("/dev/v1/sessions", json={"persona": "asha"}, headers={"X-ForKhatri-Dev-Token": "nope"})
    assert wrong.status_code == 403 and error_code(wrong) == "dev_token_invalid" and "session_token" not in wrong.text

    token = _dev_tools_token()
    if len(token) >= 32:
        test_mode = client.post(
            "/dev/v1/sessions", json={"persona": "milavn-moderator"}, headers={"X-ForKhatri-Dev-Token": token}
        )
        assert test_mode.status_code == 200 and "set-cookie" not in test_mode.headers
        body = test_mode.json()
        moderator_cookie = {"Cookie": f"{body['cookie_name']}={body['session_token']}"}
        assert client.get("/v1/session", headers=moderator_cookie).json()["member"]["display_name"] == "Milavn Moderator"
        owner = client.post("/dev/v1/sessions", json={"persona": "krishna"}, headers={"X-ForKhatri-Dev-Token": token})
        assert owner.status_code == 403 and error_code(owner) == "owner_reserved"
        client.post("/v1/auth/sign-out", json={"everywhere": False}, headers=moderator_cookie)
    client.post("/v1/auth/sign-out", json={"everywhere": False}, headers=second_cookie)


def test_validation_errors_use_the_contract_shape(client: httpx.Client) -> None:
    response = client.post("/v1/auth/code/verify", json={"challenge_id": "x", "code": "12"})
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["code"] == "validation_failed" and set(detail["fields"]) == {"challenge_id", "code"}
