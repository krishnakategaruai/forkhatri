"""Runtime configuration for the Milavn service.

# [TR-CROSSCUT-01..04, TR03, TR29] Every runtime value binds to a key that
# `07a-db-implementation/.env.example` or `config/external_services.yaml`
# already owns, so no code carries a literal those files decide.
# Approach: pydantic-settings reads the database implementation's own `.env`
# (identical DB_* names) plus this service's own `.env` for service-level
# values (API port, CORS origins, dev-identity switch). Per this project's
# config-placeholder convention, CHANGE_ME/REPLACE_ME values are placeholders
# a real deployment overwrites as a pure data change.
# Traces to: TR-CROSSCUT-01, TR-CROSSCUT-02, TR03, TR29, architecture.md §3.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_MODULE_DIR = Path(__file__).resolve().parents[3]
_DB_IMPL_DIR = _MODULE_DIR / "07a-db-implementation"
_SERVICE_DIR = _MODULE_DIR / "milavn-service"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(_DB_IMPL_DIR / ".env", _SERVICE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Core connection (07a-db-implementation/.env) -------------------------
    db_host: str = "localhost"
    db_port: int = 5433
    db_name: str = "forkhatridb"
    # The application connects ONLY as the non-owning role — there is no owner
    # credential on this object, so an owner connection cannot be built by
    # mistake (MODULE-ARCHITECTURE-STANDARD §4, first RLS failure mode).
    db_app_user: str = "milavn_app"
    db_app_password: str = "milavn_app_dev_password"
    db_pool_max_connections: int = 20

    # --- Service ----------------------------------------------------------------
    api_host: str = "127.0.0.1"
    # 8001 per the parallel-development rule (8000 is Mangaly's). Run WITHOUT
    # `--reload` on Windows: uvicorn's reloader spawns the real server as a
    # multiprocessing child that inherits the listening socket, and when the
    # reloader dies that orphan keeps serving stale code on the port ("ghost
    # listener"). Restart the process after code changes instead.
    api_port: int = 8001
    api_debug: bool = False
    cors_allowed_origins: list[str] = ["http://localhost:3001", "http://127.0.0.1:3001"]
    # Public web origin used inside QR codes and share links generated server-side.
    web_base_url: str = "http://localhost:3001"

    # --- Identity (platform-owned) ----------------------------------------------
    # Authentication is owned by the ForKhatri platform's Identity & Trust
    # Service (ADR-004; docs/ParentApp/07-tech-reqs.md TR12-TR15). The browser
    # holds one HttpOnly cookie (`platform_session_cookie`); Milavn resolves it
    # server-to-server with its own service credentials. Values come from
    # `milavn-service/.env` (see `.env.example`); the key default is a placeholder.
    platform_identity_url: str = "http://localhost:8100"
    platform_service_name: str = "milavn"
    platform_service_key: str = "CHANGE_ME"
    platform_session_cookie: str = "fk_session"
    # Where a signed-out person is sent to sign in (the ForKhatri web entrance).
    forkhatri_entrance_url: str = "http://localhost:3100"
    # Legacy development stand-in: `X-Milavn-Member-Id` header / `milavn_member`
    # cookie resolved against `config/dev_identities.json`. Off by default;
    # only automated tests switch it on explicitly (TR15.5). Never true in a
    # real deployment.
    dev_identity_enabled: bool = False

    # --- Idempotency / rate limiting (§4b / §4c) -------------------------------
    idempotency_key_ttl_days: int = 7
    rate_limit_report_max: int = 10
    rate_limit_report_window_seconds: int = 3600
    rate_limit_create_max: int = 20
    rate_limit_create_window_seconds: int = 3600
    rate_limit_participation_max: int = 60
    rate_limit_participation_window_seconds: int = 600

    # --- Payments (FR102) ---------------------------------------------------------
    # Money moves only through Payment Services (MOD06); Milavn keeps references.
    # "none" (default): paid activities say payments are not switched on yet.
    # "sandbox": development test checkout, refused unless API and web are on localhost.
    # "payment_services": MOD06 HTTP contract (components/payments/interface.py).
    payments_provider: str = "none"
    payment_services_url: str = "http://localhost:8016"  # MOD06's reserved API port; MOD06 is not built yet
    payment_services_key: str = "CHANGE_ME"
    payment_services_webhook_key: str = "CHANGE_ME"

    # --- External services (config/external_services.yaml placeholders) -------
    map_tile_vendor: str = "maptiler"
    map_tile_api_key: str = "REPLACE_ME_MAPTILER_API_KEY"
    geocoding_vendor: str = "opencage"
    geocoding_api_key: str = "REPLACE_ME_OPENCAGE_API_KEY"

    @property
    def sqlalchemy_url(self) -> str:
        return f"postgresql+asyncpg://{self.db_app_user}:{self.db_app_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def payments_sandbox_allowed(self) -> bool:
        local = ("http://localhost", "http://127.0.0.1")
        return self.api_host in ("127.0.0.1", "localhost") and self.web_base_url.startswith(local)

    @property
    def media_root(self) -> Path:
        return _SERVICE_DIR / ".local-media"

    @property
    def dev_identities_path(self) -> Path:
        return Path(__file__).resolve().parent / "dev_identities.json"


@lru_cache
def get_settings() -> Settings:
    return Settings()
