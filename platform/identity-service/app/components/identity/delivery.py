"""One-time-code delivery (TR19).

Providers, chosen per channel in settings:

- `console`: logs the code for local development only; the production guard in
  settings refuses to start with it.
- `disabled`: the channel is not offered. Requests fail with
  `503 delivery_unavailable` before any challenge is created (production SMS
  until an SMS provider is funded; phone members sign in with a password).
- `resend` (email only): Resend's HTTP API, `POST https://api.resend.com/emails`
  with a bearer key. The challenge id is sent as `Idempotency-Key`, so a retried
  request can never deliver two different emails for one challenge.

The code and the full destination are never logged; only the masked hint is.
"""

from __future__ import annotations

import logging

import httpx

from app.components.identity.identifiers import Identifier
from app.config.settings import Settings

logger = logging.getLogger("identity.delivery")


class DeliveryUnavailable(RuntimeError):
    pass


def _provider(settings: Settings, identifier: Identifier) -> str:
    return settings.sms_provider if identifier.kind == "phone" else settings.email_provider


def channel_available(settings: Settings, identifier: Identifier) -> bool:
    """False when this identifier's channel cannot deliver a code in this environment."""
    provider = _provider(settings, identifier)
    if provider == "console":
        return True
    if provider == "resend":
        return identifier.kind == "email" and bool(settings.resend_api_key) and bool(settings.email_from)
    return False


def _email_body(code: str, minutes: int) -> tuple[str, str, str]:
    subject = "Your ForKhatri sign-in code"
    text = (
        f"Your ForKhatri sign-in code is {code}. It expires in {minutes} minutes.\n"
        f"आपका ForKhatri साइन-इन कोड {code} है। यह {minutes} मिनट में समाप्त हो जाएगा।\n"
        f"మీ ForKhatri సైన్-ఇన్ కోడ్ {code}. ఇది {minutes} నిమిషాల్లో ముగుస్తుంది.\n\n"
        "If you did not ask for this code, you can ignore this email. ForKhatri will never ask you to share it."
    )
    html = (
        '<div style="font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;max-width:480px;margin:auto;padding:24px;color:#1b1b1f">'
        '<p style="margin:0 0 8px">Your ForKhatri sign-in code</p>'
        f'<p style="font-size:32px;letter-spacing:8px;font-weight:700;margin:0 0 16px">{code}</p>'
        f'<p style="margin:0 0 4px">It expires in {minutes} minutes.</p>'
        f'<p style="margin:0 0 4px">आपका ForKhatri साइन-इन कोड {code} है। यह {minutes} मिनट में समाप्त हो जाएगा।</p>'
        f'<p style="margin:0 0 16px">మీ ForKhatri సైన్-ఇన్ కోడ్ {code}. ఇది {minutes} నిమిషాల్లో ముగుస్తుంది.</p>'
        '<p style="color:#666;font-size:13px;margin:0">If you did not ask for this code, ignore this email. '
        "ForKhatri will never ask you to share it.</p></div>"
    )
    return subject, text, html


async def _send_resend(
    settings: Settings,
    identifier: Identifier,
    code: str,
    idempotency_key: str,
    transport: httpx.AsyncBaseTransport | None,
) -> None:
    subject, text, html = _email_body(code, max(1, settings.otp_ttl_seconds // 60))
    payload = {"from": settings.email_from, "to": [identifier.value], "subject": subject, "text": text, "html": html}
    headers = {"Authorization": f"Bearer {settings.resend_api_key}", "Idempotency-Key": idempotency_key}
    try:
        async with httpx.AsyncClient(timeout=settings.delivery_timeout_seconds, transport=transport) as client:
            response = await client.post(settings.resend_api_url, json=payload, headers=headers)
    except httpx.HTTPError as exc:
        logger.error("email delivery to %s failed: %s", identifier.hint(), type(exc).__name__)
        raise DeliveryUnavailable("The email provider could not be reached.") from exc
    if response.status_code >= 300:
        try:
            reason = str(response.json().get("name", ""))[:80]
        except ValueError:
            reason = ""
        logger.error("email delivery to %s rejected: HTTP %s %s", identifier.hint(), response.status_code, reason)
        raise DeliveryUnavailable("The email provider rejected the message.")
    logger.info("email code sent to %s", identifier.hint())


async def send_code(
    settings: Settings,
    identifier: Identifier,
    code: str,
    *,
    idempotency_key: str,
    transport: httpx.AsyncBaseTransport | None = None,
) -> None:
    provider = _provider(settings, identifier)
    if provider == "console":
        logger.warning("DEVELOPMENT one-time code for %s: %s", identifier.hint(), code)
        return
    if provider == "resend" and channel_available(settings, identifier):
        await _send_resend(settings, identifier, code, idempotency_key, transport)
        return
    raise DeliveryUnavailable(f"No {identifier.kind} delivery provider is configured.")
