"""Auth endpoints — FR090/FR092/FR093/FR101/FR095.

The HTTP layer is deliberately thin: it maps requests onto Identity Bridge's
`interface.py` and renders responses. It contains no credential logic and no
account lookup of its own.

[SP093] `generic_auth_error()` below is the single shared function every
anti-enumeration response goes through. TR093's Constraints call for exactly
this — one function rather than each endpoint formatting an equivalent-looking
body, since two hand-written "identical" responses drift the moment one is
edited.

[ADR-010] Every string a human reads goes through `app.i18n.translate()`
against the caller's resolved `Locale`, never a literal English string. This
was added after a review found every message in this file hardcoded to
English regardless of the frontend's own, already-built translation layer —
`translate()` mirrors that layer's own English-fallback rule (a missing Hindi/
Telugu key silently renders English, never a raw key or an error).
"""

from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field, field_validator

from app.api.deps import AppSettings, DbSession, Locale, get_current_session_token
from app.components.identity_bridge import interface as identity
from app.i18n import translate

router = APIRouter(prefix="/auth", tags=["auth"])

SESSION_COOKIE = "mangaly_session"


def generic_auth_error(lang: str) -> HTTPException:
    """[SP093/TR093] The one identical failure response for every auth path.

    Same status, same (localized) body, for wrong credential and unknown
    identifier alike. Callers raise this rather than composing their own, so
    the responses cannot drift apart later — in wording or in translation.
    """
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=translate("auth.error.invalidCredentials", lang),
    )


class SignUpRequest(BaseModel):
    """[DEC-V1-012] `credential` is optional — the primary sign-up path is
    identifier + OTP only. Supplying one opts into the secondary password
    login path (see `LoginRequest` below) from the start, but nothing in the
    UI requires it."""

    identifier: str = Field(min_length=3, max_length=254)
    credential: str | None = Field(default=None, min_length=1, max_length=256)

    @field_validator("identifier")
    @classmethod
    def _strip(cls, v: str) -> str:
        return v.strip()


class LoginRequest(BaseModel):
    """[DEC-V1-012] The SECONDARY login path — reached only via the login
    screen's "use password instead" link, for an account that has one set.
    The primary path is `/auth/login/otp/request` + `/auth/otp/verify`."""

    identifier: str = Field(min_length=3, max_length=254)
    credential: str = Field(min_length=1, max_length=256)


class LoginOtpRequest(BaseModel):
    identifier: str = Field(min_length=3, max_length=254)


class SignUpResponse(BaseModel):
    """[SP092] One shape for both outcomes.

    There is no `already_registered` field, and there cannot be one: the route
    never puts the distinction into the response model, so it cannot leak by a
    later template change either.
    """

    status: Literal["verification_sent"] = "verification_sent"
    message: str


class SessionResponse(BaseModel):
    account_id: str
    expires_at: str


def _set_session_cookie(response: Response, token: str, secure: bool) -> None:
    """[SP090] HttpOnly/SameSite cookie, not JavaScript-readable storage.

    Token theft via script injection or a shared device is a real exposure for
    a web client, so the session token is never placed anywhere the page's own
    JS can read it.
    """
    response.set_cookie(
        SESSION_COOKIE,
        token,
        httponly=True,
        secure=secure,
        samesite="lax",
        max_age=int(identity.SESSION_TTL.total_seconds()),
        path="/",
    )


@router.post("/signup", response_model=SignUpResponse, status_code=status.HTTP_202_ACCEPTED)
async def sign_up(
    body: SignUpRequest,
    session: DbSession,
    settings: AppSettings,
    lang: Locale,
) -> SignUpResponse:
    """[FR092/TR092] Create an account, or silently do nothing if it exists.

    Always 202 with the same body. See `identity.sign_up` for why this deviates
    from UX03's inline "already registered" error and why UI03 already set that
    precedent.
    """
    try:
        result = await identity.sign_up(
            session, identifier=body.identifier, credential=body.credential
        )
    except identity.WeakCredential as exc:
        # Safe to report: describes the credential just typed, not who exists.
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=translate(exc.key, lang, **exc.params),
        ) from exc

    # [FR095] `identity.sign_up` already issued and delivered a verification
    # code when `created` is true. The already-registered out-of-band notice
    # for `created=False` is Notification Bridge's job, not built in this pass
    # — the response is identical either way regardless (SP092).
    _ = result.created

    return SignUpResponse(message=translate("auth.signup.sent", lang))


@router.post("/login", response_model=SessionResponse)
async def log_in(
    body: LoginRequest,
    response: Response,
    session: DbSession,
    settings: AppSettings,
    lang: Locale,
) -> SessionResponse:
    """[FR093/TR093] Authenticate and open a session."""
    try:
        token = await identity.log_in(
            session, identifier=body.identifier, credential=body.credential
        )
    except identity.RateLimited as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=translate("auth.error.rateLimited", lang),
            headers={"Retry-After": str(exc.retry_after_seconds)},
        ) from exc
    except identity.AuthError as exc:
        raise generic_auth_error(lang) from exc

    _set_session_cookie(response, token.token, secure=settings.session_cookie_secure)
    return SessionResponse(
        account_id=str(token.account_id), expires_at=token.expires_at.isoformat()
    )


@router.post(
    "/login/otp/request", status_code=status.HTTP_202_ACCEPTED, response_model=SignUpResponse
)
async def request_login_otp(
    body: LoginOtpRequest, session: DbSession, lang: Locale
) -> SignUpResponse:
    """[FR093/DEC-V1-012] The PRIMARY login path: request a one-time code.

    Same response whether or not the identifier is registered — see
    `identity.request_login_otp`. Verification happens through the same
    `/auth/otp/verify` endpoint every other OTP purpose uses, with
    `purpose=login`.
    """
    try:
        await identity.request_login_otp(session, identifier=body.identifier)
    except identity.RateLimited as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=translate("auth.error.rateLimited", lang),
            headers={"Retry-After": str(exc.retry_after_seconds)},
        ) from exc
    return SignUpResponse(message=translate("auth.signup.sent", lang))


class PasswordResetRequest(BaseModel):
    identifier: str = Field(min_length=3, max_length=254)


@router.post(
    "/reset/request", status_code=status.HTTP_202_ACCEPTED, response_model=SignUpResponse
)
async def request_password_reset(
    body: PasswordResetRequest, session: DbSession, lang: Locale
) -> SignUpResponse:
    """[FR094/TR094] Request a password-reset code.

    Same response whether or not the identifier is registered — see
    `identity.request_password_reset`. Reuses the OTP purpose `password_reset`
    (FR095's own mechanism, as FR094 itself specifies), confirmed through
    `/auth/reset/confirm` below rather than the generic `/auth/otp/verify`,
    since verifying there would consume the single-use code before the new
    password is ever set.
    """
    try:
        await identity.request_password_reset(session, identifier=body.identifier)
    except identity.RateLimited as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=translate("auth.error.rateLimited", lang),
            headers={"Retry-After": str(exc.retry_after_seconds)},
        ) from exc
    return SignUpResponse(message=translate("auth.reset.requested", lang))


class PasswordResetConfirmRequest(BaseModel):
    identifier: str = Field(min_length=3, max_length=254)
    code: str = Field(min_length=4, max_length=8)
    new_credential: str = Field(min_length=1, max_length=256)


class PasswordResetConfirmResponse(BaseModel):
    outcome: identity.OtpOutcome
    message: str | None = None


@router.post("/reset/confirm", response_model=PasswordResetConfirmResponse)
async def confirm_password_reset(
    body: PasswordResetConfirmRequest, session: DbSession, lang: Locale
) -> PasswordResetConfirmResponse:
    """[FR094/TR094] Verify the reset code and set the new password in one
    step — see `identity.confirm_password_reset`'s docstring for why this
    cannot be split into a separate verify-then-confirm pair."""
    try:
        outcome = await identity.confirm_password_reset(
            session,
            identifier=body.identifier,
            code=body.code,
            new_credential=body.new_credential,
        )
    except identity.WeakCredential as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=translate(exc.key, lang, **exc.params),
        ) from exc
    if outcome is not identity.OtpOutcome.VERIFIED:
        return PasswordResetConfirmResponse(outcome=outcome)
    return PasswordResetConfirmResponse(
        outcome=outcome, message=translate("auth.reset.success", lang)
    )


@router.get("/me", response_model=SessionResponse)
async def me(
    session: DbSession,
    token: Annotated[str | None, Depends(get_current_session_token)],
    lang: Locale,
) -> SessionResponse:
    """[FR090/TR090] Resolve the current session for launch routing."""
    not_authenticated = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=translate("auth.error.notAuthenticated", lang),
    )
    if token is None:
        raise not_authenticated
    account_id = await identity.validate_session(session, token)
    if account_id is None:
        raise not_authenticated
    return SessionResponse(account_id=str(account_id), expires_at="")


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def log_out(
    response: Response,
    session: DbSession,
    token: Annotated[str | None, Depends(get_current_session_token)],
) -> None:
    """[FR101/TR101] Revoke the session server-side, then clear the cookie."""
    if token:
        await identity.log_out(session, token)
    response.delete_cookie(SESSION_COOKIE, path="/")


class OtpVerifyRequest(BaseModel):
    identifier: str = Field(min_length=3, max_length=254)
    code: str = Field(min_length=4, max_length=8)
    purpose: identity.OtpPurpose = identity.OtpPurpose.SIGNUP


class OtpResendRequest(BaseModel):
    identifier: str = Field(min_length=3, max_length=254)
    purpose: identity.OtpPurpose = identity.OtpPurpose.SIGNUP


class OtpVerifyResponse(BaseModel):
    """[UX04] `outcome` stays a machine-readable code, not localized prose —
    it carries the distinct reason UX04's copy needs ("wrong code" vs "expired"
    vs "too many attempts"), and the FRONTEND localizes it via its own
    `auth:otp.error.*` keys, the same as any other client-rendered UI state.
    SP095's uniform-response requirement is about hiding whether an *account*
    exists, not about hiding *why* a code the caller already proved they
    received was rejected; see `identity.verify_otp`'s docstring."""

    outcome: identity.OtpOutcome
    account_id: str | None = None
    expires_at: str | None = None


@router.post("/otp/verify", response_model=OtpVerifyResponse)
async def verify_otp(
    body: OtpVerifyRequest, response: Response, session: DbSession, settings: AppSettings
) -> OtpVerifyResponse:
    """[FR095/TR095/TS212/TS213] Verify a one-time code."""
    result = await identity.verify_otp(
        session, identifier=body.identifier, code=body.code, purpose=body.purpose
    )
    if result.session is not None:
        _set_session_cookie(response, result.session.token, secure=settings.session_cookie_secure)
        return OtpVerifyResponse(
            outcome=result.outcome,
            account_id=str(result.session.account_id),
            expires_at=result.session.expires_at.isoformat(),
        )
    return OtpVerifyResponse(outcome=result.outcome)


@router.post("/otp/resend", status_code=status.HTTP_202_ACCEPTED, response_model=SignUpResponse)
async def resend_otp(body: OtpResendRequest, session: DbSession, lang: Locale) -> SignUpResponse:
    """[FR095/SP095] Resend, rate-limited. Same response whether or not the
    identifier is registered — see `identity.request_otp_resend`."""
    try:
        await identity.request_otp_resend(
            session, identifier=body.identifier, purpose=body.purpose
        )
    except identity.ResendRateLimited as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=translate("auth.error.otpRateLimited", lang),
            headers={"Retry-After": str(exc.retry_after_seconds)},
        ) from exc
    return SignUpResponse(message=translate("auth.signup.resent", lang))
