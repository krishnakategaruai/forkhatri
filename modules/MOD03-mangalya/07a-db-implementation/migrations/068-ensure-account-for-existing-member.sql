-- =============================================================================
-- 068 — Reach a family member who is on ForKhatri but has not opened Mangalya.
--
-- WHY: a brother making a profile for his sister is refused when her number is
--   already a ForKhatri member (her account is hers). He then asks to join her
--   Home Circle, but people search and the invite only see Mangalya accounts,
--   and she has none until she first opens Mangalya — so "no account" was shown
--   for someone who plainly exists. The platform confirms the member; this
--   gives her a Mangalya member-link row on her own member id (no profile), so
--   the request reaches her and she sees it when she opens Mangalya.
--
-- Idempotent: an existing row is left untouched. Must be called by another
--   signed-in account, never by the member themselves.
-- =============================================================================

CREATE OR REPLACE FUNCTION mangaly_identity.ensure_account_for_member(
    p_member_id uuid,
    p_phone     text,
    p_name      text
) RETURNS uuid
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = mangaly_identity, pg_temp
AS $$
BEGIN
    IF current_setting('mangaly.account_id', true) IS NULL
       OR current_setting('mangaly.account_id', true) = ''
       OR current_setting('mangaly.account_id', true)::uuid = p_member_id THEN
        RAISE EXCEPTION 'ensure_account_for_member: must be called by another signed-in account';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM mangaly_identity.account WHERE id = p_member_id) THEN
        INSERT INTO mangaly_identity.account (id, phone_identifier, status, display_name)
        VALUES (p_member_id, p_phone, 'active', p_name);
    END IF;
    RETURN p_member_id;
END;
$$;
REVOKE ALL ON FUNCTION mangaly_identity.ensure_account_for_member(uuid, text, text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_identity.ensure_account_for_member(uuid, text, text) TO mangaly_app;
