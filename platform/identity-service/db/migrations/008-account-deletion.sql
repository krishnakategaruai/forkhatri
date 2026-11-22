-- =============================================================================
-- 008 — Account deletion (kind A, "Delete my ForKhatri account")
-- Contract: docs/ParentApp/ACCOUNT-DELETION.md. Additive; re-running is safe.
--
-- Run as identity_owner:
--   psql -h localhost -p 5433 -U identity_owner -d forkhatri_identity -f db/migrations/008-account-deletion.sql
--
--   * identity.deletion_job / deletion_job_module: one job per deleted member and one
--     row per module's erase result. Neither holds the member id once the job is done
--     (member_id is nulled; only the one-way tombstone hash remains).
--   * identity.finalize_member_deletion(): SECURITY DEFINER routine that removes every
--     identity row of the member in one transaction and rewrites the append-only audit
--     log to the tombstone. The runtime role has no DELETE grant on identity tables and
--     stays that way: this function is its only door.
--   * governance.audit_event gains actor_tombstone / target_tombstone. The append-only
--     trigger still blocks every change except the erase function's tombstone rewrite.
-- =============================================================================

CREATE TABLE IF NOT EXISTS identity.deletion_job (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  -- Nulled when the job completes (nothing identifies the member afterwards).
  member_id     uuid,
  tombstone     text NOT NULL UNIQUE,
  status        text NOT NULL DEFAULT 'running' CHECK (status IN ('running', 'done')),
  requested_at  timestamptz NOT NULL DEFAULT now(),
  deadline_at   timestamptz NOT NULL,
  completed_at  timestamptz,
  receipt       jsonb
);
CREATE INDEX IF NOT EXISTS idx_deletion_job_open ON identity.deletion_job (requested_at) WHERE status = 'running';
CREATE UNIQUE INDEX IF NOT EXISTS uq_deletion_job_member ON identity.deletion_job (member_id) WHERE member_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS identity.deletion_job_module (
  job_id          uuid NOT NULL REFERENCES identity.deletion_job(id) ON DELETE CASCADE,
  module_key      text NOT NULL,
  status          text NOT NULL DEFAULT 'pending'
                  CHECK (status IN ('pending', 'running', 'done', 'nothing_to_delete', 'partial', 'failed')),
  attempts        integer NOT NULL DEFAULT 0,
  next_attempt_at timestamptz NOT NULL DEFAULT now(),
  claimed_until   timestamptz,
  last_error      text,
  result          jsonb,
  updated_at      timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (job_id, module_key)
);

GRANT SELECT, INSERT, UPDATE ON identity.deletion_job TO identity_app;
GRANT SELECT, INSERT, UPDATE ON identity.deletion_job_module TO identity_app;

-- Audit rows keep a one-way tombstone where a deleted member's id used to be.
ALTER TABLE governance.audit_event ADD COLUMN IF NOT EXISTS actor_tombstone text;
ALTER TABLE governance.audit_event ADD COLUMN IF NOT EXISTS target_tombstone text;

-- Append-only stays absolute, except the tombstone rewrite performed by the erase
-- function (it sets a transaction-local flag and runs as the table owner).
CREATE OR REPLACE FUNCTION governance.audit_is_append_only() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP = 'UPDATE'
     AND current_user = 'identity_owner'
     AND coalesce(current_setting('identity.erasing', true), '') = 'on' THEN
    RETURN NEW;
  END IF;
  RAISE EXCEPTION 'governance.audit_event is append-only';
END $$;

CREATE OR REPLACE FUNCTION identity.finalize_member_deletion(p_member uuid, p_tombstone text)
RETURNS jsonb
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog, identity, governance, registry, platform
AS $$
DECLARE
  v_phone   text;
  v_email   text;
  v_counts  jsonb := '{}'::jsonb;
  n         integer;
BEGIN
  SELECT phone_e164, email INTO v_phone, v_email FROM identity.member WHERE id = p_member FOR UPDATE;
  IF NOT FOUND THEN
    RETURN jsonb_build_object('member', 0);
  END IF;
  IF EXISTS (
    SELECT 1 FROM governance.role_assignment
     WHERE member_id = p_member AND revoked_at IS NULL AND (ends_at IS NULL OR ends_at > now())
  ) THEN
    RAISE EXCEPTION 'member holds an administrative role' USING ERRCODE = 'P0001';
  END IF;

  PERFORM set_config('identity.erasing', 'on', true);

  -- Audit log: the member's id becomes the tombstone; free text about them is dropped.
  UPDATE governance.audit_event
     SET target_tombstone = p_tombstone, target_member_id = NULL,
         subject = NULL, note = NULL, details = '{}'::jsonb
   WHERE target_member_id = p_member;
  GET DIAGNOSTICS n = ROW_COUNT;
  v_counts := v_counts || jsonb_build_object('audit_rows_about_member', n);
  UPDATE governance.audit_event
     SET actor_tombstone = p_tombstone, actor_member_id = NULL, ip = NULL
   WHERE actor_member_id = p_member;
  GET DIAGNOSTICS n = ROW_COUNT;
  v_counts := v_counts || jsonb_build_object('audit_rows_by_member', n);
  PERFORM set_config('identity.erasing', 'off', true);

  -- Other people's records that merely point at the member.
  UPDATE governance.chapter SET created_by = NULL WHERE created_by = p_member;
  UPDATE governance.role_assignment SET granted_by = NULL WHERE granted_by = p_member;
  UPDATE governance.role_assignment SET revoked_by = NULL WHERE revoked_by = p_member;
  UPDATE governance.suspension SET created_by = NULL WHERE created_by = p_member;
  UPDATE governance.suspension SET lifted_by = NULL WHERE lifted_by = p_member;
  UPDATE governance.approval_request SET decided_by = NULL
   WHERE decided_by = p_member AND target_member_id <> p_member AND requested_by <> p_member;

  DELETE FROM governance.approval_request WHERE target_member_id = p_member OR requested_by = p_member;
  GET DIAGNOSTICS n = ROW_COUNT;
  v_counts := v_counts || jsonb_build_object('approval_requests', n);
  DELETE FROM governance.role_assignment WHERE member_id = p_member;
  GET DIAGNOSTICS n = ROW_COUNT;
  v_counts := v_counts || jsonb_build_object('role_assignments', n);
  DELETE FROM governance.suspension WHERE member_id = p_member;
  GET DIAGNOSTICS n = ROW_COUNT;
  v_counts := v_counts || jsonb_build_object('suspensions', n);

  DELETE FROM identity.session WHERE member_id = p_member;
  GET DIAGNOSTICS n = ROW_COUNT;
  v_counts := v_counts || jsonb_build_object('sessions', n);
  DELETE FROM identity.password_credential WHERE member_id = p_member;
  GET DIAGNOSTICS n = ROW_COUNT;
  v_counts := v_counts || jsonb_build_object('password_credentials', n);
  DELETE FROM registry.member_module_entry WHERE member_id = p_member;
  GET DIAGNOSTICS n = ROW_COUNT;
  v_counts := v_counts || jsonb_build_object('module_entries', n);
  DELETE FROM identity.otp_challenge WHERE identifier IN (v_phone, v_email);
  GET DIAGNOSTICS n = ROW_COUNT;
  v_counts := v_counts || jsonb_build_object('one_time_codes', n);
  DELETE FROM platform.rate_limit_counter
   WHERE bucket_key IN ('code:id:' || v_phone, 'code:id:' || v_email, 'password:id:' || v_phone, 'password:id:' || v_email);
  DELETE FROM identity.member WHERE id = p_member;
  v_counts := v_counts || jsonb_build_object('member', 1);
  RETURN v_counts;
END $$;

ALTER FUNCTION identity.finalize_member_deletion(uuid, text) OWNER TO identity_owner;
REVOKE ALL ON FUNCTION identity.finalize_member_deletion(uuid, text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION identity.finalize_member_deletion(uuid, text) TO identity_app;
