-- [IMP-ADMIN — Admin & Governance Console, ADR-012 / TR-PLAT-01, 2026-09-29]
-- Session-granted operator permissions.
--
-- The platform's identity service now answers a session resolve with
-- `admin_scopes` (for example ["vyapar.moderate","vyapar.verify"]). The
-- ForKhatri identity adapter maps them onto Vyapar's own permission names
-- (moderation, content, verification, commercial, analytics) and the request
-- connection carries them next to vyapar.authz_context, in a second
-- transaction-local setting written by the same code path (app/db.py
-- get_conn, set_config(..., true) — never a plain SET):
--
--     vyapar.authz_permissions = {"member_id": "<id>", "permissions": ["moderation", ...]}
--
-- The value names the member it was granted to. session_permissions()
-- returns the permissions only while vyapar.authz_context is still that same
-- member, so a code path that briefly switches the context to another member
-- (contracts' dispute resolution acts as the client for one step) never
-- carries the operator's permissions across. Unknown permission names are
-- dropped: only the five names the members.operator_permissions CHECK allows
-- can ever be granted this way.
--
-- is_operator(permission) keeps its signature, so every existing RLS policy
-- picks this up unchanged. Either source grants access:
--   * the member row (is_operator AND permission in operator_permissions), or
--   * the session (permission in session_permissions(); NULL = any).
-- A missing, empty or other-member setting grants nothing.
-- Additive and idempotent. Traces to: TR-PLAT-01, ADR-012, TR050, FR47, FR48, FR49
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION vyapar_identity.session_permissions()
RETURNS text[]
LANGUAGE sql STABLE
SET search_path = vyapar_identity, pg_temp
AS $$
  SELECT CASE
           WHEN g IS NULL OR jsonb_typeof(g) <> 'object' OR jsonb_typeof(g -> 'permissions') <> 'array'
             OR (g ->> 'member_id') IS DISTINCT FROM current_setting('vyapar.authz_context', true)
             OR coalesce(current_setting('vyapar.authz_context', true), '') = ''
           THEN '{}'::text[]
           ELSE ARRAY(
             SELECT p FROM jsonb_array_elements_text(g -> 'permissions') AS p
              WHERE p = ANY (ARRAY['verification','content','commercial','analytics','moderation'])
           )
         END
    FROM (SELECT nullif(current_setting('vyapar.authz_permissions', true), '')::jsonb AS g) s;
$$;
COMMENT ON FUNCTION vyapar_identity.session_permissions() IS
  '[TR-PLAT-01/ADR-012] Operator permissions granted by the platform session (identity resolve admin_scopes), read from the transaction-local vyapar.authz_permissions setting. Empty unless the setting names the member vyapar.authz_context currently holds.';

CREATE OR REPLACE FUNCTION vyapar_identity.is_operator(p_permission text)
RETURNS boolean
LANGUAGE sql STABLE SECURITY DEFINER
SET search_path = vyapar_identity, pg_temp
AS $$
  SELECT EXISTS (
           SELECT 1 FROM vyapar_identity.members m
            WHERE m.id = current_setting('vyapar.authz_context', true)
              AND m.is_operator
              AND (p_permission IS NULL OR p_permission = ANY (m.operator_permissions))
         )
      OR (CASE WHEN p_permission IS NULL
               THEN cardinality(vyapar_identity.session_permissions()) > 0
               ELSE p_permission = ANY (vyapar_identity.session_permissions())
          END);
$$;
COMMENT ON FUNCTION vyapar_identity.is_operator(text) IS
  '[MODULE-ARCHITECTURE-STANDARD §4/§5, extended by migration 024] Shared RLS operator-bypass helper. True when the member row grants the permission (is_operator AND permission in operator_permissions) OR the platform session granted it (session_permissions()). p_permission NULL means "any operator permission".';

GRANT EXECUTE ON FUNCTION vyapar_identity.session_permissions() TO vyapar_app;
GRANT EXECUTE ON FUNCTION vyapar_identity.is_operator(text) TO vyapar_app;

-- [IMP-ADMIN] Verification decisions write the listing's verification label
-- (verification_state, claim, state active_verified <-> active_unverified).
-- listings_visibility only lets the owner or a 'content' operator write, so a
-- 'verification'-only operator (the platform's vyapar.verify scope) was
-- refused by RLS on verify/reject/clearer-copy. This extra permissive UPDATE
-- policy admits exactly that operator for updates; reads and inserts are
-- unchanged. (A member-row operator always held both permissions, which hid
-- the gap.)
DROP POLICY IF EXISTS listings_verification_operator_update ON vyapar_listings.listings;
CREATE POLICY listings_verification_operator_update ON vyapar_listings.listings
  FOR UPDATE
  USING (vyapar_identity.is_operator('verification'))
  WITH CHECK (vyapar_identity.is_operator('verification'));
