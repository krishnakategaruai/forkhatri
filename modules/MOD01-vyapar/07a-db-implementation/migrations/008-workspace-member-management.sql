-- [TR034 gaps, found during Step 9 design of slice 9 — fixed forward.]
--
-- `workspace_members_visible` (001) admits a row to its inviter, its invitee,
-- an active collaborator of that listing, or a commercial operator. Two real
-- consequences for FR34:
--  Gap 1: the listing OWNER is none of those for a row an ADMIN created — the
--    owner is not themselves a `workspace_members` row — so the owner could
--    not see their own team once an admin had invited anyone.
--  Gap 2: for the same reason the owner could not revoke an admin-invited
--    role, which breaks FR34's "the owner may revoke a role at any time".
--
-- Fix: two narrow SECURITY DEFINER functions that resolve authority through
-- the same `workspace_context()` the Authorization Engine uses, so the role
-- rules live in exactly one place. Both refuse anyone without the team
-- capability (owner or admin, and only while the entitlement is active).
SET search_path TO pg_temp;

CREATE OR REPLACE FUNCTION vyapar_commercial.workspace_members_for(p_listing_id uuid)
RETURNS TABLE(id uuid, member_id text, phone_masked text, role text, state text,
              invited_by text, invited_at timestamptz, accepted_at timestamptz, expires_at timestamptz, display_name text)
LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path = vyapar_commercial, pg_temp AS $$
DECLARE v_role text;
BEGIN
  SELECT w.role INTO v_role FROM vyapar_commercial.workspace_context(p_listing_id) w;
  IF coalesce(v_role, 'none') NOT IN ('owner', 'admin', 'operator') THEN RAISE EXCEPTION 'not_a_workspace_member'; END IF;
  RETURN QUERY
    SELECT wm.id, wm.member_id,
           -- never the full phone back out: last 4 only, same masking rule as
           -- verification identifiers (FR08/SP008)
           '••••' || right(wm.phone, 4),
           wm.role, wm.state, wm.invited_by, wm.invited_at, wm.accepted_at, wm.expires_at,
           CASE WHEN m.anonymized THEN NULL ELSE m.display_name END
      FROM vyapar_commercial.workspace_members wm
      LEFT JOIN vyapar_identity.members m ON m.id = wm.member_id
     WHERE wm.listing_id = p_listing_id::text
     ORDER BY wm.invited_at;
END;
$$;

CREATE OR REPLACE FUNCTION vyapar_commercial.set_member_role_state(
  p_member_row_id uuid, p_new_state text, p_new_role text
) RETURNS TABLE(member_id text, listing_id text, role text, state text)
LANGUAGE plpgsql SECURITY DEFINER SET search_path = vyapar_commercial, pg_temp AS $$
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
         role = coalesce(p_new_role, role),
         revoked_at = CASE WHEN p_new_state = 'revoked' THEN now() ELSE revoked_at END
   WHERE id = wm.id;
  RETURN QUERY SELECT wm.member_id, wm.listing_id, coalesce(p_new_role, wm.role), p_new_state;
END;
$$;

GRANT EXECUTE ON FUNCTION vyapar_commercial.workspace_members_for(uuid) TO vyapar_app;
GRANT EXECUTE ON FUNCTION vyapar_commercial.set_member_role_state(uuid, text, text) TO vyapar_app;

-- Gap 3 (FR34): an invite / role change must reach the other member, but the
-- notifications policy only lets a member insert their OWN rows. Narrow
-- definer: the caller must hold owner/admin authority for that listing, and
-- the recipient must be a row of that same workspace. Text arrives
-- pre-translated for en/hi/te; the recipient's own language is chosen here.
CREATE OR REPLACE FUNCTION vyapar_commercial.notify_workspace_member(
  p_listing_id uuid, p_recipient text, p_template text, p_texts jsonb, p_link text, p_idem text
) RETURNS boolean
LANGUAGE plpgsql SECURITY DEFINER SET search_path = vyapar_commercial, pg_temp AS $$
DECLARE
  v_role text;
  v_lang text;
  v_id uuid;
BEGIN
  SELECT w.role INTO v_role FROM vyapar_commercial.workspace_context(p_listing_id) w;
  IF coalesce(v_role, 'none') NOT IN ('owner', 'admin') THEN RAISE EXCEPTION 'role_not_allowed'; END IF;
  IF NOT EXISTS (SELECT 1 FROM vyapar_commercial.workspace_members wm
                  WHERE wm.listing_id = p_listing_id::text AND wm.member_id = p_recipient) THEN
    RAISE EXCEPTION 'not_a_workspace_member';
  END IF;
  SELECT m.language INTO v_lang FROM vyapar_identity.members m WHERE m.id = p_recipient;
  v_lang := coalesce(v_lang, 'en');
  INSERT INTO vyapar_integration.notifications (member_id, kind, template_id, title, body, link, params, idempotency_key)
  VALUES (p_recipient, p_template, p_template,
          coalesce(p_texts -> v_lang ->> 'title', p_texts -> 'en' ->> 'title'),
          coalesce(p_texts -> v_lang ->> 'body', p_texts -> 'en' ->> 'body'),
          p_link, jsonb_build_object('listing_id', p_listing_id), p_idem)
  ON CONFLICT (idempotency_key) DO NOTHING
  RETURNING id INTO v_id;
  RETURN v_id IS NOT NULL;
END;
$$;

GRANT EXECUTE ON FUNCTION vyapar_commercial.notify_workspace_member(uuid, text, text, jsonb, text, text) TO vyapar_app;
