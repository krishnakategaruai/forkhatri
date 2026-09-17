-- =============================================================================
-- 014 — mangaly_identity.account becomes Mangaly's member-link table for the
--       ForKhatri platform identity.
--
-- WHY (2026-09-14, product-owner decision; binding contract
-- docs/ParentApp/07-tech-reqs.md TR10/TR11/TR15/TR23):
-- ForKhatri is one app with one sign-in. The platform Identity & Trust Service
-- (platform/identity-service, database forkhatri_identity) now owns members,
-- credentials, OTP and sessions. Mangaly's interim credential store — named
-- technical debt since IA092 / v1-decisions.md "Known technical debt" — is
-- retired as a sign-in mechanism. It is NOT dropped:
--
--   * Every Mangaly table keys people by `account_id` = account.id. TR23
--     imported every active Mangaly account into the platform with its id
--     unchanged, so platform `member_id == account_id` and no foreign key in
--     any of the 14 schemas is rewritten.
--   * TR11 says a module keeps its own per-member link row and creates it
--     just-in-time on first entry. `account` already is that row (every RLS
--     policy in mangaly_identity keys on it, and Home Circle reads the
--     member's own phone/email from it to match invitations), so it is
--     reused rather than a parallel "member" table being introduced.
--
-- WHAT CHANGES:
--   1. `credential_hash` becomes nullable. A platform member proves who they
--      are to the platform, never to Mangaly, so a new link row has no
--      Mangaly credential at all. Previously a random never-exposed hash was
--      generated purely to satisfy NOT NULL (DEC-V1-012); NULL now states the
--      truth. `lookup_by_identifier()` still returns the column, and the
--      interim verifier treats NULL exactly like an unknown account (dummy
--      verify → reject), so the legacy path — disabled by default — cannot be
--      used to sign in to a credential-less row.
--   2. `account_has_identifier` keeps requiring a phone or email, except for
--      a row whose status is 'deleted'. A retired row must be able to give
--      its identifiers up (see 3) without violating the CHECK.
--   3. `ensure_platform_account(member_id, phone, email)` — the one write the
--      module's Identity Bridge performs on every platform-authenticated
--      request (TR15 step 4). SECURITY DEFINER because it runs BEFORE
--      `mangaly.account_id` is bound — creating/syncing the link row is what
--      makes that binding meaningful — the same chicken-and-egg shape
--      migrations 003/004 already documented for sign-up and session lookup.
--      Its inputs are not caller-supplied: they are the claims the Identity &
--      Trust Service returned for a session token over the authenticated
--      internal API (TR14), so the function trusts them as verified.
--
-- IDENTIFIER CONFLICTS (UNIQUE phone/email):
--   * Another account in 'pending_verification' holding the identifier is an
--     abandoned interim sign-up whose identifier was never proven (TR23 did
--     not import those). The platform has now verified the identifier for
--     this member, so the pending row is retired (status 'deleted',
--     identifiers nulled) rather than blocking a real member's entry.
--   * Another 'active' (or 'locked') account holding it is a genuine conflict
--     between two proven owners. That is never resolved silently: the
--     function raises SQLSTATE MGL09 ("platform_identity_conflict") and the
--     service fails the request closed for operations to reconcile.
--   * The member's own row in 'locked' or 'deleted' raises MGL03
--     ("platform_account_not_active"): platform sign-in must not silently
--     undo a Mangaly lock or deletion.
--
-- Concurrency: a transaction-scoped advisory lock keyed on the member id
-- serialises two first-entry requests for the same new member (the web app
-- fires several API calls in parallel on first load).
--
-- Idempotent and safe to re-run.
-- =============================================================================

ALTER TABLE mangaly_identity.account
  ALTER COLUMN credential_hash DROP NOT NULL;

ALTER TABLE mangaly_identity.account
  DROP CONSTRAINT IF EXISTS account_has_identifier;
ALTER TABLE mangaly_identity.account
  ADD CONSTRAINT account_has_identifier
  CHECK (phone_identifier IS NOT NULL OR email_identifier IS NOT NULL OR status = 'deleted');

COMMENT ON TABLE mangaly_identity.account IS
  '[TR092 → ForKhatri TR11] Mangaly member-link row, id = platform member_id. Interim credential columns retained for history; sign-in is owned by the ForKhatri Identity & Trust Service (migration 014). PII-sensitive.';

CREATE OR REPLACE FUNCTION mangaly_identity.ensure_platform_account(
  p_member_id uuid,
  p_phone     text,
  p_email     text
)
RETURNS uuid
LANGUAGE plpgsql
VOLATILE
SECURITY DEFINER
SET search_path = mangaly_identity, pg_temp
AS $$
DECLARE
  v_phone  text := NULLIF(btrim(p_phone), '');
  v_email  text := NULLIF(lower(btrim(p_email)), '');
  v_own    mangaly_identity.account%ROWTYPE;
  v_exists boolean;
  v_holder record;
BEGIN
  IF p_member_id IS NULL THEN
    RAISE EXCEPTION 'platform_identity_invalid: member id is required'
      USING ERRCODE = '22004';
  END IF;
  IF v_phone IS NULL AND v_email IS NULL THEN
    -- Mangaly must receive identifiers (SERVICES_RECEIVING_IDENTIFIERS):
    -- Home Circle invitations match on them. Missing identifiers are a
    -- platform configuration error, never something to paper over.
    RAISE EXCEPTION 'platform_identity_invalid: member % has no phone or email in its claims', p_member_id
      USING ERRCODE = '22004';
  END IF;

  PERFORM pg_advisory_xact_lock(hashtextextended('mangaly_identity.platform_account:' || p_member_id::text, 0));

  SELECT * INTO v_own FROM mangaly_identity.account WHERE id = p_member_id FOR UPDATE;
  -- Captured once: FOUND is overwritten by every later statement and loop.
  v_exists := FOUND;

  IF v_exists AND v_own.status IN ('locked', 'deleted') THEN
    RAISE EXCEPTION 'platform_account_not_active: Mangaly account % is %', p_member_id, v_own.status
      USING ERRCODE = 'MGL03';
  END IF;

  -- Fast path: nothing to change (the overwhelmingly common request).
  IF v_exists
     AND v_own.status = 'active'
     AND v_own.phone_identifier IS NOT DISTINCT FROM v_phone
     AND v_own.email_identifier IS NOT DISTINCT FROM v_email THEN
    RETURN p_member_id;
  END IF;

  -- Free the identifiers from any OTHER account that holds them.
  FOR v_holder IN
    SELECT a.id, a.status
    FROM mangaly_identity.account a
    WHERE a.id <> p_member_id
      AND ((v_phone IS NOT NULL AND a.phone_identifier = v_phone)
        OR (v_email IS NOT NULL AND a.email_identifier = v_email))
    FOR UPDATE
  LOOP
    IF v_holder.status = 'pending_verification' THEN
      UPDATE mangaly_identity.account
         SET status = 'deleted',
             phone_identifier = NULL,
             email_identifier = NULL,
             updated_at = now()
       WHERE id = v_holder.id;
    ELSE
      RAISE EXCEPTION 'platform_identity_conflict: an identifier of member % is held by another % Mangaly account', p_member_id, v_holder.status
        USING ERRCODE = 'MGL09',
              HINT = 'Two proven owners of one identifier must be reconciled by operations; nothing was changed.';
    END IF;
  END LOOP;

  IF v_exists THEN
    -- Sync to the platform's current verified identifiers. An own row still in
    -- 'pending_verification' is activated: the platform has now proven it.
    UPDATE mangaly_identity.account
       SET phone_identifier = v_phone,
           email_identifier = v_email,
           status = 'active',
           identifier_verified_at = now(),
           updated_at = now()
     WHERE id = p_member_id;
  ELSE
    -- Just-in-time link row (TR11). No Mangaly credential exists for it.
    INSERT INTO mangaly_identity.account
      (id, phone_identifier, email_identifier, credential_hash, status, identifier_verified_at)
    VALUES
      (p_member_id, v_phone, v_email, NULL, 'active', now());
  END IF;

  RETURN p_member_id;
END;
$$;

COMMENT ON FUNCTION mangaly_identity.ensure_platform_account(uuid, text, text) IS
  '[ForKhatri TR11/TR15] Create or sync the member-link row for a platform-authenticated member (id = member_id) from Identity & Trust Service claims. Retires a conflicting pending_verification account; raises MGL09 platform_identity_conflict for a conflicting active/locked account and MGL03 platform_account_not_active for an own locked/deleted row. SECURITY DEFINER because it runs before mangaly.account_id is bound. Frozen surface: changes need security review.';

REVOKE ALL ON FUNCTION mangaly_identity.ensure_platform_account(uuid, text, text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_identity.ensure_platform_account(uuid, text, text) TO mangaly_app;
