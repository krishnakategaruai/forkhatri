-- =============================================================================
-- Milavn (MOD02) — migration 010: feedback upsert grant. Run as milavn_owner.
--
-- FR066 lets a participant revise their own private feedback (one row per
-- member per occurrence, `feedback_unique`). The application upserts, so the
-- runtime role needs UPDATE alongside SELECT/INSERT; the existing
-- `feedback_self_or_internal` policy (FOR ALL, member-self) still scopes it.
-- =============================================================================
GRANT UPDATE ON milavn_trust.feedback TO milavn_app;
