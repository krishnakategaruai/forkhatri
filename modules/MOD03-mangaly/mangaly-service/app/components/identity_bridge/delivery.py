"""OTP delivery — the one seam between this component and a real SMS/email provider.

FR095's own Assumptions state delivery infrastructure is Common Platform
(`modules.md`'s notification-delivery Shared Concern); this module still needs
one concrete implementation to actually run against for local development and
testing, per this project's config-placeholder convention (real config
structure now, drop in real values, which is exactly what happened here).

This is intentionally the ONLY place an issued/resent challenge's code is
read outside `otp.py` itself. Swapping providers later means changing this
one function, not any caller.

**Known limitation, stated plainly rather than silently accepted:** India's
DLT (TRAI) regime requires an SMS's sender header and content template be
pre-registered before delivery to Indian mobile numbers; `SMS_DLT_TEMPLATE_ID_OTP`
is still a placeholder (no template registered yet), and a Twilio trial
account cannot complete that registration on its own. A message sent to an
Indian number through this path may therefore be silently dropped by the
carrier even when Twilio itself reports success. The code is ALSO always
logged server-side regardless of the Twilio call's outcome, specifically so
testing is never blocked on a delivery path this module does not yet fully
control end-to-end (TR095's own fallback-channel finding names this exact
class of gap).
"""

from __future__ import annotations

import logging

import httpx

from app.components.identity_bridge.otp import IssuedChallenge, mask_identifier
from app.config.settings import get_settings

logger = logging.getLogger(__name__)

_TWILIO_MESSAGES_URL = "https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"


def _normalise_for_allowlist(identifier: str) -> str:
    return identifier.strip().replace(" ", "")


def _is_dev_allowed(identifier: str, settings) -> bool:  # type: ignore[no-untyped-def]
    """[Dev-mode instruction] Only send a REAL SMS to an explicitly allowed
    number during development. Every other identifier still gets the log-only
    fallback in `deliver()` below — this only gates the live Twilio call, so
    testing against any identifier keeps working without spending trial quota
    or risking a message to a number that isn't actually under test.
    """
    allowed = {
        _normalise_for_allowlist(n)
        for n in settings.twilio_dev_allowed_numbers.split(",")
        if n.strip()
    }
    return _normalise_for_allowlist(identifier) in allowed


def _otp_body(challenge: IssuedChallenge, ttl_minutes: int) -> str:
    return (
        f"Your Mangaly verification code is {challenge.code}. "
        f"It expires in {ttl_minutes} minutes. Never share this code with anyone."
    )


async def _send_via_twilio(to_identifier: str, body: str) -> None:
    settings = get_settings()
    url = _TWILIO_MESSAGES_URL.format(sid=settings.twilio_account_sid)
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            url,
            data={"To": to_identifier, "From": settings.twilio_from_number, "Body": body},
            auth=(settings.twilio_account_sid, settings.twilio_auth_token),
        )
    if response.is_error:
        # Never include `body` here beyond what's already logged elsewhere —
        # this line is the one place a Twilio failure reason is recorded, and
        # the auth credentials never appear in `response.request` logging
        # because httpx does not echo Authorization header values on error.
        logger.error(
            "Twilio send failed status=%s response=%s", response.status_code, response.text[:300]
        )
    else:
        logger.info("Twilio accepted message sid=%s", response.json().get("sid"))


async def deliver(identifier: str, challenge: IssuedChallenge) -> None:
    settings = get_settings()
    masked = mask_identifier(identifier)
    ttl_minutes = max(1, settings.otp_ttl_seconds // 60)

    # Always logged, regardless of provider outcome — see module docstring's
    # "Known limitation" note on India DLT routing.
    logger.warning(
        "OTP for %s (%s channel): %s (dev/fallback log, independent of provider result)",
        masked,
        challenge.channel.value,
        challenge.code,
    )

    if settings.sms_provider == "CHANGE_ME":
        return

    if settings.sms_provider == "twilio":
        if challenge.channel.value != "sms" or "@" in identifier:
            # Twilio here is configured for SMS; an email-channel challenge has
            # no delivery path yet and relies entirely on the log above.
            return
        if not _is_dev_allowed(identifier, settings):
            logger.info(
                "Twilio send skipped for %s — not on TWILIO_DEV_ALLOWED_NUMBERS "
                "(log above still has the code)",
                masked,
            )
            return
        try:
            await _send_via_twilio(identifier, _otp_body(challenge, ttl_minutes))
        except httpx.HTTPError as exc:
            logger.error("Twilio request failed: %s", exc)
        return

    raise NotImplementedError(
        f"SMS_PROVIDER={settings.sms_provider!r} has no delivery implementation yet"
    )
