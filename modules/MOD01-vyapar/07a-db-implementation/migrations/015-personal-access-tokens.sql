-- [IMP37 — Refactor B: agent and API access] Personal access tokens.
--
-- Owner's direction (2026-09-21): "I need more API-like connections, as many
-- as possible, so we can have agents working on top of Vyapar easily." An
-- agent (the vyapar-mcp server, a script, another platform) acts ON BEHALF OF
-- one member with a scoped, revocable credential. The credential never
-- widens what the member could do: every request it makes still runs under
-- that member's vyapar.authz_context, so RLS decides exactly as it does for
-- the member's own web session.
--
-- Storage rules:
--   * The token itself is never stored. Only sha256(token) is kept, plus a
--     short display prefix so the member can tell their tokens apart.
--   * A member sees and revokes only their own tokens (RLS, self-only — not
--     even operators read another member's credentials).
--   * Authentication must find a token by its hash BEFORE any authz_context
--     exists, which a self-only policy correctly blocks. That lookup goes
--     through one narrow SECURITY DEFINER function under the same
--     constraints as 013's functions (MODULE-ARCHITECTURE-STANDARD §4):
--     exact match on a full identifier (the hash), minimal projection,
--     validity (not revoked, not expired, member not deleted) enforced
--     inside the function, at most one row, search_path pinned.
--
-- Also here: a purge function for expired rows of the shared
-- vyapar_platform.idempotency_key store, which the new Idempotency-Key
-- middleware writes with a 24-hour expiry. Its RLS is member-self only, so a
-- background job cannot see expired rows without this narrow path.
-- Traces to: REFACTOR-PLAN.md §B, FR49 (audit attribution), TR050, SP050

CREATE TABLE IF NOT EXISTS vyapar_integration.access_tokens (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  member_id    text NOT NULL,                       -- no cross-schema FK (convention 3)
  name         text NOT NULL CHECK (char_length(name) BETWEEN 1 AND 80),
  token_hash   text NOT NULL UNIQUE CHECK (token_hash ~ '^[0-9a-f]{64}$'),
  token_prefix text NOT NULL,
  scopes       text[] NOT NULL CHECK (
                 cardinality(scopes) > 0 AND scopes <@ ARRAY[
                   'read','opportunities:write','listings:write','enquiries:write',
                   'reviews:write','partnerships:write','notifications:write'
                 ]::text[]),
  created_at   timestamptz NOT NULL DEFAULT now(),
  expires_at   timestamptz NOT NULL,
  last_used_at timestamptz,
  revoked_at   timestamptz,
  CHECK (expires_at > created_at)
);
CREATE INDEX IF NOT EXISTS access_tokens_member_idx ON vyapar_integration.access_tokens (member_id, created_at DESC);
COMMENT ON TABLE vyapar_integration.access_tokens IS
  '[IMP37] Personal access tokens for agents/API clients. sha256 hash only, never plaintext. Self-only RLS; authentication lookup via resolve_access_token().';

ALTER TABLE vyapar_integration.access_tokens ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS access_tokens_self_only ON vyapar_integration.access_tokens;
CREATE POLICY access_tokens_self_only ON vyapar_integration.access_tokens
  USING (member_id = current_setting('vyapar.authz_context', true))
  WITH CHECK (member_id = current_setting('vyapar.authz_context', true));

-- No DELETE grant: revocation is an UPDATE of revoked_at, so the record of a
-- credential that once acted for a member survives for the audit trail.
GRANT SELECT, INSERT, UPDATE ON vyapar_integration.access_tokens TO vyapar_app;

CREATE OR REPLACE FUNCTION vyapar_integration.resolve_access_token(p_token_hash text)
RETURNS TABLE(token_id uuid, member_id text, scopes text[], expires_at timestamptz)
LANGUAGE plpgsql VOLATILE SECURITY DEFINER
SET search_path = vyapar_integration, pg_temp
AS $$
DECLARE
  v_row vyapar_integration.access_tokens%ROWTYPE;
BEGIN
  IF p_token_hash IS NULL OR p_token_hash !~ '^[0-9a-f]{64}$' THEN
    RETURN;
  END IF;
  SELECT t.* INTO v_row
    FROM vyapar_integration.access_tokens t
   WHERE t.token_hash = p_token_hash
     AND t.revoked_at IS NULL
     AND t.expires_at > now()
     AND EXISTS (
       SELECT 1 FROM vyapar_identity.members m
        WHERE m.id = t.member_id AND NOT m.anonymized AND m.deleted_at IS NULL
     )
   LIMIT 1;
  IF NOT FOUND THEN
    RETURN;
  END IF;
  -- last_used_at is advisory (shown in the token list); written at most once
  -- a minute so a busy agent does not turn every read into a row update.
  IF v_row.last_used_at IS NULL OR v_row.last_used_at < now() - interval '1 minute' THEN
    UPDATE vyapar_integration.access_tokens SET last_used_at = now() WHERE id = v_row.id;
  END IF;
  token_id := v_row.id;
  member_id := v_row.member_id;
  scopes := v_row.scopes;
  expires_at := v_row.expires_at;
  RETURN NEXT;
END;
$$;
COMMENT ON FUNCTION vyapar_integration.resolve_access_token(text) IS
  '[IMP37] Pre-authorization token lookup by sha256 hash. Returns at most one valid (unrevoked, unexpired, live member) row; minimal projection.';

REVOKE ALL ON FUNCTION vyapar_integration.resolve_access_token(text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION vyapar_integration.resolve_access_token(text) TO vyapar_app;

CREATE OR REPLACE FUNCTION vyapar_platform.purge_expired_idempotency_keys()
RETURNS integer
LANGUAGE plpgsql VOLATILE SECURITY DEFINER
SET search_path = vyapar_platform, pg_temp
AS $$
DECLARE
  v_count integer;
BEGIN
  IF current_setting('vyapar.service_role', true) IS DISTINCT FROM 'dispatcher' THEN
    RAISE EXCEPTION 'purge_expired_idempotency_keys() is dispatcher-only';
  END IF;
  DELETE FROM vyapar_platform.idempotency_key WHERE expires_at < now();
  GET DIAGNOSTICS v_count = ROW_COUNT;
  RETURN v_count;
END;
$$;
REVOKE ALL ON FUNCTION vyapar_platform.purge_expired_idempotency_keys() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION vyapar_platform.purge_expired_idempotency_keys() TO vyapar_app;
