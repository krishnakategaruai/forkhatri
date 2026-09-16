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


@lru_cache
def get_settings() -> Settings:
    return Settings()
