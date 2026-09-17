-- 035 — Date-bound circles for temple visits and travel (FR125).
--
-- WHY (2026-09-18, owner request): a temple yatra or a group trip is not an open-ended community —
-- it exists around a specific date (or date range), it needs planning (which day, who's coming, a
-- shared kitty for the bus or the offering), and once it happens it becomes something to remember,
-- not something to keep discovering. Circles already have polls (FR120), drives (FR124), a board and
-- chapters (FR123) — the only thing missing was a first-class date. Rather than a new object, a
-- temple/travel circle is an ordinary circle with a type and an optional date range, so it gets
-- everything a circle already has for free.
--
--   circle_type            + 'temple', 'travel' — both open (joinable directly, like interest/local)
--   circle.starts_on       when it happens (temple: the day; travel: the trip's first day)
--   circle.ends_on         travel's last day; null for a single day
--
-- Discovery excludes a date-bound circle once its date has passed (nothing to plan any more), but
-- `mine()` still shows it — a member's own past yatra or trip stays visible, the same way a past
-- activity stays on their profile.

DO $$ BEGIN
  ALTER TYPE milavn_circle.circle_type ADD VALUE IF NOT EXISTS 'temple';
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
  ALTER TYPE milavn_circle.circle_type ADD VALUE IF NOT EXISTS 'travel';
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

ALTER TABLE milavn_circle.circle
  ADD COLUMN IF NOT EXISTS starts_on date,
  ADD COLUMN IF NOT EXISTS ends_on date;

DO $$ BEGIN
  ALTER TABLE milavn_circle.circle ADD CONSTRAINT circle_dates_sane CHECK (ends_on IS NULL OR starts_on IS NULL OR ends_on >= starts_on);
EXCEPTION WHEN duplicate_table OR duplicate_object THEN NULL;
END $$;
