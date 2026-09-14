-- 013 — Photo ordering for the profile photo grid
--
-- The profile hub's photo grid (Hinge/Bumble pattern: up to six photos,
-- long-press and drag to reorder) needs a stable, person-chosen order.
-- profile_media previously had only `is_primary`, so every photo after the
-- main one could only ever be ordered by upload time.
--
-- Additive and backwards-compatible: existing rows are numbered by their
-- current effective order (primary first, then oldest first), and the
-- column defaults to 0 so the existing creation-time INSERT path keeps
-- working unchanged. `is_primary` remains the source of truth for the main
-- photo; the application keeps the primary photo at sort_order 0.

ALTER TABLE mangaly_profile.profile_media
    ADD COLUMN IF NOT EXISTS sort_order integer NOT NULL DEFAULT 0;

WITH ranked AS (
    SELECT id,
           row_number() OVER (
               PARTITION BY profile_id
               ORDER BY is_primary DESC, created_at
           ) - 1 AS rn
    FROM mangaly_profile.profile_media
)
UPDATE mangaly_profile.profile_media m
SET sort_order = ranked.rn
FROM ranked
WHERE ranked.id = m.id;
