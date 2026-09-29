-- 005 — Home Circle relationship taxonomy (fixes forward against Step 7a)
--
-- [Gap found live, 2026-09-13] FR008's own acceptance criterion requires
-- "acceptance creates a membership record with the relationship claim," and
-- UX12's wireframe requires a relationship-role picker before an invite is
-- sent — but neither `07a-er-model.md` nor migration 001 gave `invitation`
-- or `membership` anywhere to store it. M01-C (Home Circle Conceptual Model)
-- ss4 names the exact taxonomy: Candidate/Parent/Sibling/Relative, with the
-- real relationship (mother/father/brother/cousin/...) recorded separately
-- from that functional category. This migration adds the category only —
-- the free-text real relationship, if ever needed, belongs in a later,
-- separate column, not invented here.
--
-- Raised against Step 7a, ER Model & Database Implementation, for
-- ratification; resolved forward here per this module's established
-- "fix forward with a new migration, never edit applied history" rule
-- (MODULE-ARCHITECTURE-STANDARD.md ss3).

CREATE TYPE mangaly_home_circle.relationship_type AS ENUM (
    'parent',
    'sibling',
    'relative'
);

-- Captured at invite time (who the inviter says the invitee will be). No
-- DEFAULT: both tables are empty pre-launch, so a bare NOT NULL is enough —
-- a default here would silently paper over a real omission once real rows
-- exist.
ALTER TABLE mangaly_home_circle.invitation
    ADD COLUMN relationship_type mangaly_home_circle.relationship_type NOT NULL;

-- Copied onto the membership row at accept time (denormalized on purpose):
-- `membership.invitation_id` is ON DELETE SET NULL, so the relationship
-- claim must survive the invitation row's own lifecycle independently.
ALTER TABLE mangaly_home_circle.membership
    ADD COLUMN relationship_type mangaly_home_circle.relationship_type NOT NULL;
