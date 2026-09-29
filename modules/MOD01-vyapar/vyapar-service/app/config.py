# [Cross-cutting / TR050] Central, typed settings loader. Every other module
# reads configuration through this one object rather than calling os.getenv()
# ad hoc, so a config key never silently drifts between files.
# Approach: pydantic-settings reads vyapar-service/.env once at process start;
# CHANGE_ME placeholders (config-placeholder convention) are loaded as plain
# strings here — validating "is this a real credential" is a deployment-time
# concern, not a startup-crash concern for local dev.
# Traces to: TR050, SP008 (encryption key placeholder), Cross-cutting §1/§2
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # [Port plan, product owner, 2026-09-15] Vyapar's dedicated ports.
    api_port: int = 8011
    web_origin: str = "http://localhost:3011"

    database_url: str = (
        "postgres://vyapar_app:vyapar_app_dev_password@localhost:5433/vyapar"
    )

    dev_mode: bool = True
    dev_default_member_id: str = "m_krishna"
    forkhatri_entrance_url: str = "https://CHANGE_ME.forkhatri.example"
    identity_service_internal_url: str = (
        "http://CHANGE_ME-identity-service.internal"
    )
    identity_service_key: str = "CHANGE_ME"
    # [IMP-ADMIN] The name this service presents to the platform
    # (X-ForKhatri-Service); the platform keys its SERVICE_KEYS by it. The
    # same key also authenticates the platform when it calls Vyapar's
    # /internal/v1 bridges (app/integrations/internal_auth.py).
    identity_service_name: str = "vyapar"
    identity_resolve_cache_seconds: int = 30
    identity_resolve_negative_cache_seconds: int = 5

    verification_identifier_encryption_key: str = "CHANGE_ME_dev_only_32_byte_key_000000"
    object_storage_signed_url_ttl_seconds: int = 300

    rate_limit_enquiry_per_day: int = 20
    rate_limit_report_per_day: int = 10
    rate_limit_notify_strong_match_per_day: int = 3
    partnership_request_pending_cap: int = 10

    # [TR027/UX16 assumption] review tags are configuration, with both
    # positive and negative tags so a "No" review can be specific.
    review_tags_positive: list[str] = [
        "on_time", "clear_pricing", "fair_price", "good_communication", "quality", "professional", "responsive", "would_hire_again",
    ]
    review_tags_negative: list[str] = ["late", "unclear_pricing", "poor_communication", "slow_response"]
    listing_active_cap_per_member: int = 20

    # [TR021 — FR21 notification matcher/digest] strong-match threshold read
    # from config (a stand-in for the `config` table's live-admin value TR021
    # names — no admin UI exists yet this session); matcher/digest interval
    # is a dev-friendly cadence (real prod cadence is an operational choice,
    # not a design one).
    notify_strong_match_threshold: float = 2.5
    notify_matcher_interval_seconds: int = 300

    # [Notifications — Web Push swap-seam, config-placeholder convention]
    # never actually invoked this session (no subscription flow exists yet)
    # — see app/notifications.py's WebPushChannel.
    vapid_public_key: str = "CHANGE_ME_vapid_public_key"
    vapid_private_key: str = "CHANGE_ME_vapid_private_key"

    # [TR051/FR51] Payment Bridge — gateway is configuration. "dev_sandbox" is
    # the labelled dev stand-in; "razorpay" uses the real hosted Payment Link
    # flow and fails closed to "payment service unavailable" while the keys
    # below are still placeholders.
    payment_gateway: str = "dev_sandbox"
    razorpay_key_id: str = "CHANGE_ME_razorpay_key_id"
    razorpay_key_secret: str = "CHANGE_ME_razorpay_key_secret"
    payment_webhook_secret: str = "CHANGE_ME_dev_payment_webhook_secret"

    # System principal for scheduled jobs / verified webhooks that must write
    # notifications (the same operator context the existing jobs use).
    dispatcher_operator_member_id: str = "m_neha_ops"

    # [TR045] HMAC key for member_pseudo — never the verification key, never logged
    analytics_pseudonym_secret: str = "CHANGE_ME_dev_analytics_pseudonym_secret"

    # [IMP37 — Refactor B] Identity adapters. Comma-separated, tried in order
    # (e.g. IDENTITY_PROVIDERS=bearer,forkhatri or bearer,dev). Empty keeps
    # the historic behaviour: "bearer,dev" when DEV_MODE is on, otherwise
    # "bearer,forkhatri". See app/integrations/identity/.
    identity_providers: str = ""

    # [IMP37] Personal access tokens for agents and API clients.
    access_token_default_days: int = 90
    access_token_max_days: int = 365
    access_token_max_active_per_member: int = 20

    # [IMP37] Outbound webhooks. The secret key encrypts stored signing
    # secrets (AES-GCM); private targets (localhost, 10.x, 192.168.x ...) are
    # allowed only in development — turn off in any shared deployment.
    integration_secret_key: str = "CHANGE_ME_dev_integration_secret_key"
    webhook_allow_private_targets: bool = True
    webhook_dispatch_interval_seconds: int = 10
    webhook_timeout_seconds: float = 5.0
    webhook_max_attempts: int = 6
    webhook_disable_after_failures: int = 25
    webhook_max_per_member: int = 10

    # [IMP37] Idempotency-Key middleware: how long a first response is kept for replay.
    idempotency_ttl_hours: int = 24

    # [IMP-B] Contact actions: the local day/hour used for call windows and
    # the daily call cap (India Standard Time as a fixed offset, so no tz
    # database is needed on the host). Country code for tel:/wa.me links.
    contact_timezone_offset_minutes: int = 330
    contact_default_country_code: str = "91"
    # [IMP-B/FR28] Count-based badges are recomputed on read once the cached
    # value is older than this (a nightly-equivalent cadence).
    badges_cache_seconds: int = 86400
    # [IMP-B/FR40] Independent 'asked_for_money' reports that pause an
    # employment opportunity and raise its case to High.
    seeker_charge_report_threshold: int = 2
    # [IMP-B/L1] Pre-accept calling: taps one caller may make per post per day.
    precall_caller_taps_per_day: int = 3

    @property
    def identity_provider_names(self) -> list[str]:
        names = [n.strip().lower() for n in self.identity_providers.split(",") if n.strip()]
        if names:
            return names
        return ["bearer", "dev" if self.dev_mode else "forkhatri"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
