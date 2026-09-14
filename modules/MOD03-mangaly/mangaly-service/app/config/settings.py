"""Runtime configuration for MangalyService.

# [SCAFFOLD] Bind every runtime value to `07a-db-implementation/.env.example`'s
# already-decided key names, so no code carries a literal that file already owns.
# Approach: pydantic-settings v2 `BaseSettings` reads the same `.env` the
# database implementation already ships, using the *identical* variable names
# (DB_APP_USER, CREDENTIAL_HASH_TIME_COST, RATE_LIMIT_LOGIN_FAILURE_MAX, ...).
# One settings object, cached, so a value is read from one place and a real
# deployment only has to drop real values into `.env` — a pure data change, per
# this project's config-placeholder convention.
# Traces to: TR017 (non-owning DB role, pool mode), TR037/TR093/TR095 (rate
# limits), TR102 (idempotency TTL), SP092/SP104 (Argon2id parameters).
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# The database implementation directory is the single source of truth for the
# `.env` file's structure; this service reads that same file rather than
# maintaining a second, drift-prone copy of the same keys.
_DB_IMPL_DIR = Path(__file__).resolve().parents[3] / "07a-db-implementation"


class Settings(BaseSettings):
    """Every value here maps 1:1 onto a key in `07a-db-implementation/.env.example`."""

    model_config = SettingsConfigDict(
        env_file=(_DB_IMPL_DIR / ".env", Path(__file__).resolve().parents[2] / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Core connection ------------------------------------------------------
    db_host: str = "localhost"
    db_port: int = 5433
    db_name: str = "mangaly"
    # [TR017] The application connects ONLY as the non-owning role. There is
    # deliberately no owner-credential field on this object: an application that
    # cannot express the owner connection cannot accidentally open one, and RLS
    # silently no-ops for a table's owner.
    db_app_user: str = "mangaly_app"
    db_app_password: str = "mangaly_app_dev_password"

    # --- Pooling (TR017 / SP017 release blocker BLK-08-01) --------------------
    db_pool_mode: Literal["session", "transaction"] = "session"
    db_pool_max_connections: int = 20

    # --- Idempotency / rate limiting (§4b / §4c) ------------------------------
    idempotency_key_ttl_days: int = 7
    rate_limit_default_window_seconds: int = 604800
    rate_limit_login_failure_max: int = 5
    rate_limit_login_failure_window_seconds: int = 900
    rate_limit_otp_resend_max_per_hour: int = 5
    rate_limit_otp_resend_min_interval_seconds: int = 30
    # SP007's own denial-of-service row (invite spam) — same weekly window as signup.
    rate_limit_home_circle_invite_max: int = 20
    # SP042's flagged gap: "tens per day, not hundreds per hour" — 30/day.
    rate_limit_connection_request_max_per_day: int = 30
    # SP049's flagged gap: generous enough not to impede real conversation.
    rate_limit_message_send_max_per_hour: int = 120
    # [DEC-V1-014, 2026-09-14] FR050 requires "no permanent, conventional
    # chat history" but explicitly leaves the exact window open pending
    # technical/legal design (its own Confidence note). 30 days is a
    # deliberate, documented placeholder — long enough that an active
    # conversation is never disrupted mid-use, short enough that "not a
    # permanent chat log" is genuinely true rather than nominal. Revisit
    # if/when legal gives an actual number.
    message_retention_days: int = 30

    # --- Credential hashing (SP092 / SP104, Argon2id, pinned in .env.example) --
    credential_hash_algorithm: Literal["argon2id"] = "argon2id"
    credential_hash_time_cost: int = 3
    credential_hash_memory_cost_kb: int = 65536
    credential_hash_parallelism: int = 4

    # --- Object storage (TR002/TR006) ----------------------------------------
    object_storage_endpoint: str = "https://CHANGE_ME.objectstorage.example"
    object_storage_bucket: str = "mangaly-media-CHANGE_ME"
    object_storage_access_key: str = "CHANGE_ME"
    object_storage_secret_key: str = "CHANGE_ME"
    object_storage_signed_url_ttl_seconds: int = 300

    # --- On-call paging (DEC-V1-009/DEC-V1-011, TR065) ------------------------
    paging_vendor: str = "pagerduty"
    pagerduty_events_api_url: str = "https://events.pagerduty.com/v2/enqueue"
    pagerduty_routing_key: str = "CHANGE_ME_tier3_4_integration_routing_key"
    pagerduty_escalation_policy_id: str = "CHANGE_ME"

    # --- Retention (DEC-V1-010) ----------------------------------------------
    retention_post_deletion_grace_days: int = 30
    retention_post_deletion_erasure_days: int = 90
    retention_pre_erasure_notice_hours: int = 48
    retention_inactive_account_ceiling_days: int = 1095
    retention_audit_log_min_days: int = 365
    retention_safety_evidence_post_case_closure_days: int = 180

    # --- SMS/OTP delivery (TR095) --------------------------------------------
    sms_provider: str = "CHANGE_ME"
    sms_dlt_template_id_otp: str = "CHANGE_ME_transactional_route_template_id"
    otp_fallback_channel: Literal["email", "whatsapp"] = "email"
    # Twilio credentials, read only when sms_provider == "twilio"
    # (identity_bridge/delivery.py). TWILIO_AUTH_TOKEN is a bearer secret for
    # the whole Twilio account — never logged, never returned in a response.
    twilio_account_sid: str = "CHANGE_ME"
    twilio_auth_token: str = "CHANGE_ME"
    twilio_from_number: str = "CHANGE_ME"
    # [Dev-mode instruction, 2026-09-13] A Twilio trial account can only send
    # to numbers verified on that trial account anyway, and every other real
    # send burns trial quota / risks texting a number that isn't actually
    # under test. Comma-separated allowlist; empty means "send to nobody real"
    # (log-only fallback still always fires — see delivery.py).
    twilio_dev_allowed_numbers: str = "+919959102491"

    # --- Identity Bridge session/OTP/reset lifetimes --------------------------
    # Not present in the DB `.env.example` (it is a database-config file); these
    # are service-level and live in `mangaly-service/.env.example` instead.
    session_ttl_days: int = 30
    otp_ttl_seconds: int = 300
    otp_max_attempts: int = 5
    otp_code_digits: int = 6
    password_reset_ttl_seconds: int = 900
    min_credential_length: int = 10
    # [SP090] Cookie Secure flag. False for local http dev only; every deployed
    # environment must set MANGALY_SESSION_COOKIE_SECURE=true, since a session
    # cookie sent over plain http is interceptable.
    session_cookie_secure: bool = False
    # [SP090] Explicit CORS allow-list for the web client's dev origins.
    cors_allowed_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://127.0.0.1:3000"]
    )

    api_debug: bool = Field(default=False)

    @property
    def sqlalchemy_url(self) -> str:
        """Async SQLAlchemy URL for the non-owning application role."""
        return (
            f"postgresql+asyncpg://{self.db_app_user}:{self.db_app_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """One cached Settings instance for the process lifetime."""
    return Settings()
