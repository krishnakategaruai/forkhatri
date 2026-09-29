-- 042 — Circles get a real cover photo (owner review 2026-09-28: the initials-on-gradient tiles
-- read as "old school"; Meetup's 2025 redesign and District are built on real photos of real
-- people). The organizer uploads it; the circle_modify policy (040) already limits the UPDATE
-- to today's organizer.
ALTER TABLE milavn_circle.circle ADD COLUMN IF NOT EXISTS cover_ref text;
