-- =============================================================================
-- 004 — Truthful audit data for development member switching
--
-- Sessions opened by the development member switcher (`POST /dev/v1/sessions`,
-- 07-tech-reqs.md "Development tools") record auth_method 'dev' instead of
-- pretending a password was checked. The value is inert in production: the
-- router that writes it is never mounted there (Settings._production_guard).
--
-- Run as identity_owner. Idempotent.
-- =============================================================================

ALTER TYPE identity.auth_method ADD VALUE IF NOT EXISTS 'dev';
