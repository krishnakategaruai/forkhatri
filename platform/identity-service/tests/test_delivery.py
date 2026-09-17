"""Code delivery providers and the production guard (07-tech-reqs.md TR19, TR24)."""

from __future__ import annotations

import json

import httpx
import pytest
from pydantic import ValidationError

from app.components.identity import delivery
from app.components.identity.identifiers import normalize
from app.config.settings import Settings

STRONG = "x" * 40
PRODUCTION = {
    "environment": "production",
    "session_cookie_name": "__Host-fk_session",
    "session_cookie_secure": True,
    "dev_expose_otp": False,
    "otp_pepper": STRONG,
    "service_keys": {"mangaly": STRONG, "milavn": STRONG},
    "sms_provider": "disabled",
    "email_provider": "resend",
    "resend_api_key": "re_test_key",
    "email_from": "ForKhatri <no-reply@forkhatri.example>",
}


def settings(**overrides: object) -> Settings:
    return Settings(_env_file=None, **{**PRODUCTION, **overrides})  # type: ignore[arg-type]


def test_production_accepts_disabled_sms_with_resend_email() -> None:
    assert settings().sms_provider == "disabled"


@pytest.mark.parametrize(
    ("overrides", "problem"),
    [
        ({"sms_provider": "console"}, "must not be console"),
        ({"email_provider": "console"}, "must not be console"),
        ({"resend_api_key": ""}, "RESEND_API_KEY"),
        ({"email_from": ""}, "EMAIL_FROM"),
        ({"otp_pepper": "short"}, "real secrets"),
        ({"session_cookie_name": "fk_session"}, "__Host-"),
        ({"session_cookie_secure": False}, "SESSION_COOKIE_SECURE"),
        ({"dev_expose_otp": True}, "DEV_EXPOSE_OTP"),
    ],
)
def test_production_guard_rejects_unsafe_settings(overrides: dict[str, object], problem: str) -> None:
    with pytest.raises(ValidationError, match=problem):
        settings(**overrides)


def test_local_http_test_relaxes_only_the_cookie_rules() -> None:
    relaxed = settings(local_http_test=True, session_cookie_name="fk_session", session_cookie_secure=False)
    assert relaxed.session_cookie_name == "fk_session"
    with pytest.raises(ValidationError, match="DEV_EXPOSE_OTP"):
        settings(local_http_test=True, dev_expose_otp=True)


def test_channel_availability() -> None:
    prod = settings()
    assert not delivery.channel_available(prod, normalize("9876543210"))
    assert delivery.channel_available(prod, normalize("a@b.in"))
    dev = Settings(_env_file=None)
    assert delivery.channel_available(dev, normalize("9876543210"))


async def test_resend_request_shape_and_secrets_stay_out_of_logs(caplog: pytest.LogCaptureFixture) -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"id": "email-id"})

    caplog.set_level("INFO")
    await delivery.send_code(
        settings(), normalize("Asha@Example.in"), "482913", idempotency_key="otp-1", transport=httpx.MockTransport(handler)
    )
    (request,) = seen
    body = json.loads(request.content)
    assert str(request.url) == "https://api.resend.com/emails"
    assert request.headers["Authorization"] == "Bearer re_test_key"
    assert request.headers["Idempotency-Key"] == "otp-1"
    assert body["to"] == ["asha@example.in"] and body["from"].startswith("ForKhatri")
    assert "482913" in body["text"] and "482913" in body["html"]
    assert "482913" not in caplog.text and "asha@example.in" not in caplog.text and "re_test_key" not in caplog.text


async def test_resend_rejection_and_network_failure_raise_delivery_unavailable() -> None:
    rejected = httpx.MockTransport(lambda _: httpx.Response(403, json={"name": "validation_error"}))
    with pytest.raises(delivery.DeliveryUnavailable):
        await delivery.send_code(settings(), normalize("a@b.in"), "123456", idempotency_key="k", transport=rejected)

    def boom(_: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("down")

    with pytest.raises(delivery.DeliveryUnavailable):
        await delivery.send_code(settings(), normalize("a@b.in"), "123456", idempotency_key="k", transport=httpx.MockTransport(boom))


async def test_disabled_sms_raises_delivery_unavailable() -> None:
    with pytest.raises(delivery.DeliveryUnavailable):
        await delivery.send_code(settings(), normalize("9876543210"), "123456", idempotency_key="k")
