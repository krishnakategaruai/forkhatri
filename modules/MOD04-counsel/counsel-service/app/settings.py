"""Runtime configuration for the Counsel service. Every environment value
comes from `.env` (see `.env.example`); nothing environment-specific is a
code default beyond the localhost development layout."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

SERVICE_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=SERVICE_DIR / ".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=False)

    api_host: str = "127.0.0.1"
    api_port: int = 8014
    web_origin: str = "http://localhost:3014"
    cors_allowed_origins: list[str] = ["http://localhost:3014", "http://127.0.0.1:3014"]

    db_host: str = "localhost"
    db_port: int = 5433
    db_name: str = "counsel"
    db_app_user: str = "counsel_app"
    db_app_password: str = "CHANGE_ME"
    db_pool_max: int = 20

    platform_identity_url: str = "http://localhost:8100"
    platform_service_name: str = "counsel"
    platform_service_key: str = "CHANGE_ME"
    platform_session_cookie: str = "fk_session"
    forkhatri_entrance_url: str = "http://localhost:3100"
    admin_member_ids: str = ""

    # mock = Counsel's built-in stand-in (default). Any other name goes through the shared
    # ForKhatri integrations library (shared/forkhatri-integrations): sandbox (local only),
    # payment_services (the future MOD06), or a vendor adapter once one is registered there.
    payment_provider: str = "mock"
    payments_webhook_secret: str = "CHANGE_ME"
    payment_services_url: str = "http://localhost:8016"
    payment_services_key: str = "CHANGE_ME"
    notification_channels: str = "inapp,log"
    # Senders for queued deliveries (NOTIFICATION_CHANNELS email/sms/whatsapp/push), from the
    # shared library: console (local only), disabled, or a vendor adapter registered there.
    sms_provider: str = "console"
    whatsapp_provider: str = "console"
    email_provider: str = "console"
    push_provider: str = "console"
    ice_servers: str = '[{"urls":"stun:stun.l.google.com:19302"}]'
    storage_root: str = ".local-files"
    max_upload_mb: int = 25

    # Encrypts consultant payout details (UPI id, account number). Must be a real
    # Fernet key in any shared deployment; generate with Fernet.generate_key().
    payout_encryption_key: str = "CHANGE_ME"

    # Private files are encrypted at rest (AES-256-GCM; 32-byte key, urlsafe base64).
    file_encryption_key: str = "CHANGE_ME"
    # Malware scanning of uploads: none | clamav (local clamd over TCP).
    malware_scanner: str = "none"
    clamd_host: str = "127.0.0.1"
    clamd_port: int = 3310

    ai_provider: str = "rules"
    anthropic_api_key: str = "CHANGE_ME"
    counsel_ai_model: str = "claude-sonnet-5"

    @property
    def dsn(self) -> str:
        return f"postgresql://{self.db_app_user}:{self.db_app_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def admin_ids(self) -> frozenset[str]:
        return frozenset(s.strip() for s in self.admin_member_ids.split(",") if s.strip())

    @property
    def ice_server_list(self) -> list[dict]:
        try:
            return json.loads(self.ice_servers)
        except json.JSONDecodeError:
            return []

    @property
    def storage_path(self) -> Path:
        p = Path(self.storage_root)
        return p if p.is_absolute() else SERVICE_DIR / p


@lru_cache
def get_settings() -> Settings:
    return Settings()
