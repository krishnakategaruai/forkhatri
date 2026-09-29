-- =============================================================================
-- 029 — A profile can carry a voice introduction (product owner, 2026-09-17).
--
-- WHY:
--   * The owner asked for "voice input, introduction". `profile_media` already
--     models photos and a (never-built) video introduction; a spoken
--     introduction is the same kind of thing — the candidate's own material,
--     attached to their profile — so it belongs in the same table rather than
--     in a new one.
--   * Hearing someone speak is identity-revealing in a way a demographic
--     snippet is not, so a voice introduction is NOT part of the
--     pre-connection card: it is served only to viewers whose media row RLS
--     already admits (the owner, or an accepted connection holding
--     `candidate_info`), exactly like a non-primary photo.
-- Idempotent: safe to re-run.
-- =============================================================================

ALTER TYPE mangaly_profile.media_type ADD VALUE IF NOT EXISTS 'audio';
