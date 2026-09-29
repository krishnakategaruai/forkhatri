-- =============================================================================
-- 005 — Admin & Governance Console: platform governance data (ARCHITECTURE.md ADR-012)
--
-- The console is one shell for the whole of ForKhatri. The platform owns only what
-- is genuinely platform-wide:
--   * who holds an administrative role, over what area, for how long
--     (role + scope + term — samaj office bearers change every year);
--   * the samaj organisation (state and city chapters) those roles are scoped to;
--   * platform suspensions (a suspended member cannot resolve a session, so every
--     module closes at once — identity.resolve_session already requires 'active');
--   * two-person approvals for the few irreversible or power-granting actions;
--   * an append-only audit log of every administrative action.
-- Module moderation data (reports, cases, verification) stays in each module and
-- is reached through the TR-PLAT-01 view contract (modules/MOD02-milavn/07-tech-reqs.md).
--
-- Run as identity_owner. Idempotent.
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS governance;

-- Samaj chapters. The national level is the platform itself (no row).
CREATE TABLE IF NOT EXISTS governance.chapter (
  key          text PRIMARY KEY CHECK (key ~ '^[a-z0-9][a-z0-9-]{1,60}$'),
  name         text NOT NULL CHECK (char_length(btrim(name)) BETWEEN 2 AND 80),
  kind         text NOT NULL CHECK (kind IN ('state', 'city')),
  parent_key   text REFERENCES governance.chapter(key),
  created_by   uuid REFERENCES identity.member(id),
  created_at   timestamptz NOT NULL DEFAULT now(),
  archived_at  timestamptz,
  CONSTRAINT chapter_city_has_parent CHECK (kind = 'state' OR parent_key IS NOT NULL)
);

-- A role held over an area for a term. Roles and their permissions are defined in
-- code (app/components/governance/roles.py); this table only records who holds what.
CREATE TABLE IF NOT EXISTS governance.role_assignment (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  member_id    uuid NOT NULL REFERENCES identity.member(id),
  role         text NOT NULL CHECK (role ~ '^[a-z_]{2,40}$'),
  scope_kind   text NOT NULL CHECK (scope_kind IN ('platform', 'module', 'chapter')),
  scope_key    text,
  title        text CHECK (title IS NULL OR char_length(title) <= 60),
  starts_at    timestamptz NOT NULL DEFAULT now(),
  ends_at      timestamptz,
  granted_by   uuid REFERENCES identity.member(id),
  grant_note   text NOT NULL CHECK (char_length(btrim(grant_note)) BETWEEN 3 AND 500),
  approval_id  uuid,
  revoked_at   timestamptz,
  revoked_by   uuid REFERENCES identity.member(id),
  revoke_note  text,
  created_at   timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT role_scope_shape CHECK ((scope_kind = 'platform') = (scope_key IS NULL)),
  CONSTRAINT role_term_order CHECK (ends_at IS NULL OR ends_at > starts_at)
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_role_assignment_live
  ON governance.role_assignment (member_id, role, scope_kind, coalesce(scope_key, ''))
  WHERE revoked_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_role_assignment_member ON governance.role_assignment (member_id) WHERE revoked_at IS NULL;

-- Platform suspension or ban. At most one open record per member; a new decision
-- lifts the previous one first (the lift is audited).
CREATE TABLE IF NOT EXISTS governance.suspension (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  member_id    uuid NOT NULL REFERENCES identity.member(id),
  kind         text NOT NULL CHECK (kind IN ('suspension', 'ban')),
  reason_code  text NOT NULL CHECK (reason_code ~ '^[a-z_]{2,40}$'),
  note         text NOT NULL CHECK (char_length(btrim(note)) BETWEEN 3 AND 1000),
  starts_at    timestamptz NOT NULL DEFAULT now(),
  ends_at      timestamptz,
  created_by   uuid REFERENCES identity.member(id),
  approval_id  uuid,
  lifted_at    timestamptz,
  lifted_by    uuid REFERENCES identity.member(id),
  lift_note    text,
  CONSTRAINT suspension_ban_is_open_ended CHECK (kind = 'suspension' OR ends_at IS NULL)
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_suspension_open ON governance.suspension (member_id) WHERE lifted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_suspension_due ON governance.suspension (ends_at) WHERE lifted_at IS NULL AND ends_at IS NOT NULL;

-- Two-person rule (maker-checker): the requester can never be the decider.
CREATE TABLE IF NOT EXISTS governance.approval_request (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kind              text NOT NULL CHECK (kind IN ('ban', 'grant_role')),
  target_member_id  uuid NOT NULL REFERENCES identity.member(id),
  payload           jsonb NOT NULL DEFAULT '{}'::jsonb,
  reason_code       text NOT NULL CHECK (reason_code ~ '^[a-z_]{2,40}$'),
  note              text NOT NULL CHECK (char_length(btrim(note)) BETWEEN 3 AND 1000),
  requested_by      uuid NOT NULL REFERENCES identity.member(id),
  requested_at      timestamptz NOT NULL DEFAULT now(),
  status            text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'declined', 'withdrawn')),
  decided_by        uuid REFERENCES identity.member(id),
  decided_at        timestamptz,
  decision_note     text,
  CONSTRAINT approval_four_eyes CHECK (decided_by IS NULL OR status = 'withdrawn' OR decided_by <> requested_by)
);
CREATE INDEX IF NOT EXISTS idx_approval_pending ON governance.approval_request (requested_at) WHERE status = 'pending';

-- Append-only audit log. The runtime role may insert and read, never change or delete;
-- the trigger stops even the owner from rewriting history by accident.
CREATE TABLE IF NOT EXISTS governance.audit_event (
  id                bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  at                timestamptz NOT NULL DEFAULT now(),
  actor_member_id   uuid REFERENCES identity.member(id),
  action            text NOT NULL CHECK (action ~ '^[a-z_.]{3,80}$'),
  target_member_id  uuid REFERENCES identity.member(id),
  module_key        text,
  subject           text,
  reason_code       text,
  note              text,
  details           jsonb NOT NULL DEFAULT '{}'::jsonb,
  ip                text
);
CREATE INDEX IF NOT EXISTS idx_audit_at ON governance.audit_event (at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_target ON governance.audit_event (target_member_id, at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_actor ON governance.audit_event (actor_member_id, at DESC);

CREATE OR REPLACE FUNCTION governance.audit_is_append_only() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'governance.audit_event is append-only';
END $$;

DROP TRIGGER IF EXISTS audit_event_append_only ON governance.audit_event;
CREATE TRIGGER audit_event_append_only
  BEFORE UPDATE OR DELETE ON governance.audit_event
  FOR EACH ROW EXECUTE FUNCTION governance.audit_is_append_only();

-- Least-privilege runtime grants.
GRANT USAGE ON SCHEMA governance TO identity_app;
GRANT SELECT, INSERT, UPDATE ON governance.chapter TO identity_app;
GRANT SELECT, INSERT, UPDATE ON governance.role_assignment TO identity_app;
GRANT SELECT, INSERT, UPDATE ON governance.suspension TO identity_app;
GRANT SELECT, INSERT, UPDATE ON governance.approval_request TO identity_app;
GRANT SELECT, INSERT ON governance.audit_event TO identity_app;
-- Admins with modules.manage may open or close a module; nothing else in the registry.
GRANT UPDATE (availability, updated_at) ON registry.module TO identity_app;
