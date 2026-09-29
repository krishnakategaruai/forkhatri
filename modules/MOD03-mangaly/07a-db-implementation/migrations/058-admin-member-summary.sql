-- =============================================================================
-- 058 — One member's Mangaly summary for the shared ForKhatri admin console
--       (ARCHITECTURE.md ADR-012; TR-PLAT-01 member summary)
--
-- WHY (2026-09-29): the platform console's member page shows each module's
-- own facts side by side (Mangaly's plan next to Vyapar's; never merged into
-- one platform plan). A plan, an order, blocks and the account row are each
-- readable under RLS only by the member themself (and a plan by their
-- circle), so a moderator needs one narrow, audited read path.
--
-- Gate: the caller must be acting as an operator in THIS transaction
-- (`mangaly.operator_role` = 'operations', bound by the API's operator
-- chokepoint), otherwise the function raises. No free text, photos or
-- identifiers leave it: counts, codes and timestamps only.
-- Idempotent.
-- =============================================================================

CREATE OR REPLACE FUNCTION mangaly_operations.admin_member_summary(p_account uuid)
RETURNS TABLE (
  has_account       boolean,
  account_status    text,
  searchable        boolean,
  suspended         boolean,
  plan_code         text,
  plan_ends_at      timestamptz,
  plan_auto_renew   boolean,
  plan_cancelled_at timestamptz,
  blocks_made       int,
  blocked_by        int,
  rm_name           text,
  last_order_status text,
  last_order_plan   text,
  last_order_total  bigint,
  last_order_at     timestamptz
)
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = mangaly_operations, pg_temp
AS $$
BEGIN
  IF COALESCE(current_setting('mangaly.operator_role', true), '') <> 'operations' THEN
    RAISE EXCEPTION 'operators only' USING ERRCODE = 'insufficient_privilege';
  END IF;
  RETURN QUERY
  SELECT
    (a.id IS NOT NULL),
    a.status::text,
    COALESCE((SELECT d.searchable FROM mangaly_discovery.discovery_profile_index d WHERE d.profile_id = p_account), false),
    mangaly_operations.is_suspended(p_account),
    s.plan_code,
    s.ends_at,
    s.auto_renew,
    s.cancelled_at,
    (SELECT count(*)::int FROM mangaly_safety.block b WHERE b.blocker_account_id = p_account),
    (SELECT count(*)::int FROM mangaly_safety.block b WHERE b.blocked_account_id = p_account),
    (SELECT r.display_name FROM mangaly_operations.rm_assignment ra
       JOIN mangaly_operations.relationship_manager r ON r.account_id = ra.rm_account_id
      WHERE ra.member_account_id = p_account AND ra.status = 'active' LIMIT 1),
    o.status::text,
    o.plan_code,
    (o.amount_paise + o.gst_paise),
    o.created_at
  FROM (SELECT p_account AS id) q
  LEFT JOIN mangaly_identity.account a ON a.id = q.id
  LEFT JOIN LATERAL (
    SELECT ps.plan_code, ps.ends_at, ps.auto_renew, ps.cancelled_at
      FROM mangaly_billing.plan_subscription ps
     WHERE ps.account_id = p_account AND ps.status = 'active'
       AND ps.started_at <= now() AND ps.ends_at > now()
     ORDER BY ps.ends_at DESC LIMIT 1
  ) s ON true
  LEFT JOIN LATERAL (
    SELECT bo.status, bo.plan_code, bo.amount_paise, bo.gst_paise, bo.created_at
      FROM mangaly_billing."order" bo
     WHERE bo.account_id = p_account
     ORDER BY bo.created_at DESC LIMIT 1
  ) o ON true;
END;
$$;
REVOKE ALL ON FUNCTION mangaly_operations.admin_member_summary(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_operations.admin_member_summary(uuid) TO mangaly_app;
