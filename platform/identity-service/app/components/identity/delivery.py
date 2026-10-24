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
- `shared`: ForKhatri's shared messaging library (shared/forkhatri-integrations),
  with the adapter named by `SHARED_SMS_SENDER` / `SHARED_EMAIL_SENDER`. This is
  where a real SMS vendor (and any other email vendor) plugs in, once, for every
  module. Its development-only `console` adapter is refused in production.

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


def _shared_sender(settings: Settings, identifier: Identifier):
    """The shared ForKhatri messaging sender for this identifier's channel (provider `shared`)."""
    from forkhatri_integrations import messaging

    channel = "sms" if identifier.kind == "phone" else "email"
    name = settings.shared_sms_sender if channel == "sms" else settings.shared_email_sender
    return messaging.get_sender(channel, name, allow_console=settings.environment != "production")


def channel_available(settings: Settings, identifier: Identifier) -> bool:
    """False when this identifier's channel cannot deliver a code in this environment."""
    provider = _provider(settings, identifier)
    if provider == "console":
        return True
    if provider == "shared":
        return _shared_sender(settings, identifier).available
    if provider == "resend":
        return identifier.kind == "email" and bool(settings.resend_api_key) and bool(settings.email_from)
    return False


def _email_body(code: str, minutes: int) -> tuple[str, str, str]:
    subject = "Your ForKhatri sign-in code"
    text = (
        f"Your ForKhatri sign-in code is {code}. It expires in {minutes} minutes.\n"
        f"आपका ForKhatri साइन-इन कोड {code} है। यह {minutes} मिनट में समाप्त हो जाएगा।\n"
        f"మీ ForKhatri సైన్-ఇన్ కోడ్ {code}. ఇది {minutes} నిమిషాల్లో ముగుస్తుంది.\n"
        f"तुमचा ForKhatri साइन-इन कोड {code} आहे. तो {minutes} मिनिटांत संपेल.\n"
        f"ನಿಮ್ಮ ForKhatri ಸೈನ್-ಇನ್ ಕೋಡ್ {code}. ಇದು {minutes} ನಿಮಿಷಗಳಲ್ಲಿ ಮುಕ್ತಾಯವಾಗುತ್ತದೆ.\n\n"
        "If you did not ask for this code, you can ignore this email. ForKhatri will never ask you to share it."
    )
    html = (
        '<div style="font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;max-width:480px;margin:auto;padding:24px;color:#1b1b1f">'
        '<p style="margin:0 0 8px">Your ForKhatri sign-in code</p>'
        f'<p style="font-size:32px;letter-spacing:8px;font-weight:700;margin:0 0 16px">{code}</p>'
        f'<p style="margin:0 0 4px">It expires in {minutes} minutes.</p>'
        f'<p style="margin:0 0 4px">आपका ForKhatri साइन-इन कोड {code} है। यह {minutes} मिनट में समाप्त हो जाएगा।</p>'
        f'<p style="margin:0 0 4px">మీ ForKhatri సైన్-ఇన్ కోడ్ {code}. ఇది {minutes} నిమిషాల్లో ముగుస్తుంది.</p>'
        f'<p style="margin:0 0 4px">तुमचा ForKhatri साइन-इन कोड {code} आहे. तो {minutes} मिनिटांत संपेल.</p>'
        f'<p style="margin:0 0 16px">ನಿಮ್ಮ ForKhatri ಸೈನ್-ಇನ್ ಕೋಡ್ {code}. ಇದು {minutes} ನಿಮಿಷಗಳಲ್ಲಿ ಮುಕ್ತಾಯವಾಗುತ್ತದೆ.</p>'
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


async def _send_shared(settings: Settings, identifier: Identifier, code: str, idempotency_key: str) -> None:
    from forkhatri_integrations import messaging

    minutes = max(1, settings.otp_ttl_seconds // 60)
    if identifier.kind == "phone":
        message = messaging.OutboundMessage(
            channel="sms", to=identifier.value, idempotency_key=idempotency_key, sensitive=True,
            body=f"{code} is your ForKhatri sign-in code. It expires in {minutes} minutes. Never share it.",
            template_id=settings.sms_dlt_template_id, template_params=(code, str(minutes)))
    else:
        subject, text, html = _email_body(code, minutes)
        message = messaging.OutboundMessage(channel="email", to=identifier.value, idempotency_key=idempotency_key,
                                            sensitive=True, subject=subject, body=text, html=html)
    result = await _shared_sender(settings, identifier).send(message)
    if not result.ok:
        logger.error("%s delivery to %s failed via %s: %s", message.channel, identifier.hint(), result.provider, result.error[:80])
        raise DeliveryUnavailable(f"The {message.channel} provider could not deliver the code.")
    logger.info("%s code sent to %s via %s", message.channel, identifier.hint(), result.provider)


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
    if provider == "shared" and channel_available(settings, identifier):
        await _send_shared(settings, identifier, code, idempotency_key)
        return
    raise DeliveryUnavailable(f"No {identifier.kind} delivery provider is configured.")
