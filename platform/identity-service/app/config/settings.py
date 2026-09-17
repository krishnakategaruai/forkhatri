"""Runtime configuration for the ForKhatri Identity & Trust Service.

Every environment-specific value binds to `.env` (placeholders in `.env.example`,
docs/ParentApp/07-tech-reqs.md TR24). Production refuses to start while any
development-only switch or placeholder secret is still in place.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

SERVICE_DIR = Path(__file__).resolve().parents[2]
LANGUAGES = ("en", "hi", "te")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=SERVICE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: Literal["development", "production"] = "development"

    db_host: str = "localhost"
    db_port: int = 5433
    db_name: str = "forkhatri_identity"
    db_app_user: str = "identity_app"
    db_app_password: str = "identity_app_dev_password"
    db_pool_size: int = 10

    api_host: str = "127.0.0.1"
    api_port: int = 8100
    cors_allowed_origins: list[str] = [
        "http://localhost:3100",
        "http://127.0.0.1:3100",
        "http://localhost:3000",
        "http://localhost:3001",
    ]

    session_cookie_name: str = "fk_session"
    session_cookie_secure: bool = False
    session_ttl_days: int = 30

    otp_pepper: str = "CHANGE_ME_dev_otp_pepper"
    otp_ttl_seconds: int = 300
    otp_max_attempts: int = 5
    otp_resend_seconds: int = 30
    otp_verified_grace_seconds: int = 600
    dev_expose_otp: bool = True
    # [TR19] console = log the code (development only); disabled = the channel is
    # not offered (`503 delivery_unavailable`); resend = Resend's HTTP email API.
    sms_provider: Literal["console", "disabled"] = "console"
    email_provider: Literal["console", "disabled", "resend"] = "console"
    resend_api_key: str = ""
    resend_api_url: str = "https://api.resend.com/emails"
    # "ForKhatri <no-reply@example.in>"; the domain must be verified in Resend.
    email_from: str = ""
    delivery_timeout_seconds: float = 10.0

    # Deployment kit local rehearsal over plain http://localhost only: lets a
    # production build use `fk_session` without Secure. Never set on a real host.
    local_http_test: bool = False

    # Development tools (07-tech-reqs.md "Development tools"): the `/dev/v1` router
    # that switches the signed-in member without a password. Mounted only when
    # ENVIRONMENT=development, DEV_TOOLS_ENABLED=true and LOCAL_HTTP_TEST is off.
    # Production refuses to start with it enabled.
    dev_tools_enabled: bool = False
    # Optional (at least 32 characters): lets non-browser tests receive the session
    # token in the response body by sending `X-ForKhatri-Dev-Token`.
    dev_tools_token: str = ""

    # [TR20] Contract defaults. Local .env may raise the per-IP and per-member
    # values because every local browser test shares 127.0.0.1 and two seeded members.
    rate_limit_window_seconds: int = 900
    rate_limit_code_per_identifier: int = 5
    rate_limit_code_per_ip: int = 30
    rate_limit_verify_per_challenge: int = 10
    rate_limit_password_per_identifier: int = 10
    rate_limit_password_per_ip: int = 30

    service_keys: dict[str, str] = {
        "mangaly": "CHANGE_ME_dev_mangaly_service_key",
        "milavn": "CHANGE_ME_dev_milavn_service_key",
    }
    services_receiving_identifiers: list[str] = ["mangaly"]

    module_entry_urls: dict[str, str] = {
        "mangaly": "http://localhost:3000",
        "milavn": "http://localhost:3001",
    }

    @property
    def dev_tools_active(self) -> bool:
        """The development member switcher is mounted only here, never in production or a rehearsal."""
        return self.environment == "development" and self.dev_tools_enabled and not self.local_http_test

    @model_validator(mode="after")
    def _production_guard(self) -> Settings:
        if self.environment != "production":
            return self
        problems: list[str] = []
        if self.dev_tools_enabled:
            problems.append("DEV_TOOLS_ENABLED must be false")
        if not self.local_http_test:
            if not self.session_cookie_secure:
                problems.append("SESSION_COOKIE_SECURE must be true")
            if not self.session_cookie_name.startswith("__Host-"):
                problems.append("SESSION_COOKIE_NAME must use the __Host- prefix")
        if self.dev_expose_otp:
            problems.append("DEV_EXPOSE_OTP must be false")
        if (
            "CHANGE_ME" in self.otp_pepper
            or len(self.otp_pepper) < 32
            or any("CHANGE_ME" in k or len(k) < 32 for k in self.service_keys.values())
        ):
            problems.append("OTP_PEPPER and SERVICE_KEYS must be real secrets of at least 32 characters")
        if "console" in (self.sms_provider, self.email_provider):
            problems.append("SMS_PROVIDER and EMAIL_PROVIDER must not be console (use a real provider or disabled)")
        if self.email_provider == "resend" and (not self.resend_api_key or "CHANGE_ME" in self.resend_api_key):
            problems.append("RESEND_API_KEY is required when EMAIL_PROVIDER=resend")
        if self.email_provider == "resend" and "@" not in self.email_from:
            problems.append("EMAIL_FROM is required when EMAIL_PROVIDER=resend")
        if problems:
            raise ValueError("; ".join(problems))
        return self

    @property
    def sqlalchemy_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.db_app_user}:{self.db_app_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
