-- [TR034 bug fix, found by the live slice-9 test — fixed forward.]
-- `set_member_role_state()` (migration 008) declares OUT parameters named
-- `role` and `state` via RETURNS TABLE, so inside its UPDATE statement those
-- names resolved to the PL/pgSQL variables instead of the table columns:
--   ERROR: column reference "role" is ambiguous
-- Revoking a role therefore returned a 500. The pragma below makes column
-- names win inside SQL statements, which is what every other function in
-- migrations 004-007 already does.
SET search_path TO pg_temp;

CREATE OR REPLACE FUNCTION vyapar_commercial.set_member_role_state(
  p_member_row_id uuid, p_new_state text, p_new_role text
) RETURNS TABLE(member_id text, listing_id text, role text, state text)
LANGUAGE plpgsql SECURITY DEFINER SET search_path = vyapar_commercial, pg_temp AS $$
#variable_conflict use_column
DECLARE
  wm vyapar_commercial.workspace_members%ROWTYPE;
  v_role text;
  v_active boolean;
BEGIN
  SELECT * INTO wm FROM vyapar_commercial.workspace_members WHERE id = p_member_row_id FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'member_not_found'; END IF;
  SELECT w.role, w.entitlement_active INTO v_role, v_active
    FROM vyapar_commercial.workspace_context(wm.listing_id::uuid) w;
  IF coalesce(v_role, 'none') NOT IN ('owner', 'admin') THEN RAISE EXCEPTION 'role_not_allowed'; END IF;
  IF NOT coalesce(v_active, false) THEN RAISE EXCEPTION 'plan_required'; END IF;
  IF p_new_state NOT IN ('revoked', 'active') THEN RAISE EXCEPTION 'invalid_state'; END IF;
  IF p_new_role IS NOT NULL AND p_new_role NOT IN ('admin', 'operator') THEN RAISE EXCEPTION 'invalid_role'; END IF;

  UPDATE vyapar_commercial.workspace_members
     SET state = p_new_state,
         role = coalesce(p_new_role, workspace_members.role),
         revoked_at = CASE WHEN p_new_state = 'revoked' THEN now() ELSE workspace_members.revoked_at END
   WHERE id = wm.id;
  RETURN QUERY SELECT wm.member_id, wm.listing_id, coalesce(p_new_role, wm.role), p_new_state;
END;
$$;

GRANT EXECUTE ON FUNCTION vyapar_commercial.set_member_role_state(uuid, text, text) TO vyapar_app;
