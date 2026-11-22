-- =============================================================================
-- 067 — Erase everything Mangalya holds about a member (account deletion).
--       Owner requirement 2026-11-22; contract: docs/ParentApp/ACCOUNT-DELETION.md;
--       inventory: modules/MOD03-mangalya/ACCOUNT-DELETION.md.
--
-- TWO ENTRY POINTS, ONE WORKER (all additive; nothing existing changes):
--   mangaly_identity.erase_account_data(account uuid)   the worker (SECURITY
--       DEFINER, owner role). Transactional (one statement = one transaction),
--       idempotent (a second call finds nothing and returns status
--       'nothing_to_delete'). Returns counts + the file references the caller
--       must remove from disk after the commit. NOT granted to the app role.
--   mangaly_identity.erase_my_data()                    member-facing: erases
--       the account bound to mangaly.account_id (the signed-in member) only.
--   mangaly_identity.erase_member_data(member uuid)     platform-facing (the
--       internal endpoint): resolves a ForKhatri member id to the Mangalya
--       account(s) it owns (own account and/or a taken-over managed account).
--
-- WHAT IT DOES (see ACCOUNT-DELETION.md for the table):
--   * HARD DELETE: account row (phone, email, credential), sessions, OTP and
--     reset rows, alias, profile + attributes + photos + documents, member
--     profile, discovery row, shortlist, daily picks, views, horoscope and
--     charts, assessments, trust layers / face match / consent / evidence,
--     Home Circle memberships, invitations, notes, hints, suggestions,
--     messages written, chat participation, connection requests and their
--     sharing/contact rows, notifications, drafts of idempotency, billing
--     sandbox orders, agent (relationship manager) profile, offline client
--     profiles, contact views/exports, support tickets, blocks.
--   * A managed profile the member made for a child who has NOT taken it over
--     is erased with the member; one the child took over stays (the link to
--     the parent is cut: created_by / managed_by become NULL).
--   * A broker's clients are detached (the assignment rows go); the clients'
--     own accounts are untouched.
--   * RETAINED, with the member's id replaced by a one-way tombstone id and no
--     free text: reports filed by or about the member, moderation cases and
--     suspensions, appeals, contact reports, paid real-money orders, plus a
--     one-line deletion receipt.
--   * REFUSED (exception MGL11) while the member holds an operator role: roles
--     must be removed first (contract, safety rails).
-- =============================================================================

CREATE TABLE IF NOT EXISTS mangaly_platform.deletion_receipt (
    id          bigserial PRIMARY KEY,
    tombstone   text        NOT NULL,
    deleted_at  timestamptz NOT NULL DEFAULT now(),
    counts      jsonb       NOT NULL
);
COMMENT ON TABLE mangaly_platform.deletion_receipt IS
  '[067] One line per erased member: one-way tombstone, date, counts. Proof that deletion happened; holds nothing identifying.';
ALTER TABLE mangaly_platform.deletion_receipt ENABLE ROW LEVEL SECURITY;
-- no policy and no grant: written only by the SECURITY DEFINER worker.

-- One-way tombstone id: stable for one member, reveals nothing.
CREATE OR REPLACE FUNCTION mangaly_identity.member_tombstone(p_id uuid)
RETURNS uuid
LANGUAGE sql IMMUTABLE
AS $$
    SELECT (substr(h, 1, 8) || '-' || substr(h, 9, 4) || '-4' || substr(h, 14, 3) || '-a'
            || substr(h, 18, 3) || '-' || substr(h, 21, 12))::uuid
      FROM (SELECT encode(sha256(convert_to('mangalya-erased:' || p_id::text, 'UTF8')), 'hex') AS h) s;
$$;
REVOKE ALL ON FUNCTION mangaly_identity.member_tombstone(uuid) FROM PUBLIC;

CREATE OR REPLACE FUNCTION mangaly_identity._bump(r jsonb, k text, n bigint)
RETURNS jsonb
LANGUAGE sql IMMUTABLE
AS $$
    SELECT CASE WHEN n IS NULL OR n = 0 THEN r
                ELSE r || jsonb_build_object(k, COALESCE((r ->> k)::bigint, 0) + n) END;
$$;
REVOKE ALL ON FUNCTION mangaly_identity._bump(jsonb, text, bigint) FROM PUBLIC;

-- ---------------------------------------------------------------------------
-- The worker.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION mangaly_identity.erase_account_data(p_account uuid)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = mangaly_identity, pg_temp
AS $$
DECLARE
    r        jsonb := '{}'::jsonb;      -- deleted counts by kind
    k        jsonb := '{}'::jsonb;      -- retained counts by kind
    v_files  text[] := ARRAY[]::text[];
    v_dirs   text[] := ARRAY[]::text[]; -- media folders named after ids
    v_prof   uuid[];
    v_ids    uuid[];
    v_re     text;
    v_tomb   uuid := mangaly_identity.member_tombstone(p_account);
    v_conn   uuid[];
    v_conv   uuid[];
    v_mem    uuid[];
    v_child  uuid;
    v_sub    jsonb;
    v_phone  text;
    v_email  text;
    v_exists boolean;
    n        bigint;
    t        text;
BEGIN
    SELECT true, phone_identifier, email_identifier INTO v_exists, v_phone, v_email
      FROM mangaly_identity.account WHERE id = p_account;

    SELECT COALESCE(array_agg(id), ARRAY[]::uuid[]) INTO v_prof
      FROM mangaly_profile.profile WHERE account_id = p_account;
    v_ids := ARRAY[p_account] || v_prof;
    v_re  := array_to_string(v_ids, '|');

    -- Nothing at all held for this account? Then this is a repeat call.
    IF v_exists IS NOT TRUE
       AND cardinality(v_prof) = 0
       AND NOT EXISTS (SELECT 1 FROM mangaly_home_circle.membership WHERE member_account_id = p_account OR candidate_profile_id = ANY (v_ids))
       AND NOT EXISTS (SELECT 1 FROM mangaly_connection.connection_request WHERE subject_account_id = p_account OR target_profile_id = ANY (v_ids) OR acting_account_id = p_account)
       AND NOT EXISTS (SELECT 1 FROM mangaly_communication.conversation_participant WHERE account_id = p_account)
       AND NOT EXISTS (SELECT 1 FROM mangaly_profile.member_profile WHERE account_id = p_account)
       AND NOT EXISTS (SELECT 1 FROM mangaly_operations.relationship_manager WHERE account_id = p_account)
       AND NOT EXISTS (SELECT 1 FROM mangaly_operations.offline_profile WHERE agent_account_id = p_account)
       AND NOT EXISTS (SELECT 1 FROM mangaly_billing."order" WHERE account_id = p_account)
       AND NOT EXISTS (SELECT 1 FROM mangaly_notification.inbox_entry WHERE recipient_account_id = p_account)
       AND NOT EXISTS (SELECT 1 FROM mangaly_identity.account_alias WHERE member_id = p_account OR account_id = p_account) THEN
        RETURN jsonb_build_object('status', 'nothing_to_delete', 'deleted', '{}'::jsonb,
                                  'retained', '{}'::jsonb, 'file_refs', '[]'::jsonb, 'dirs', '[]'::jsonb);
    END IF;

    -- Safety rail: an operator must have the role removed first.
    IF EXISTS (SELECT 1 FROM mangaly_operations.operator WHERE account_id = p_account) THEN
        RAISE EXCEPTION 'erase_refused: this member holds a moderator role; remove it first'
            USING ERRCODE = 'MGL11';
    END IF;

    -- 1. Profiles this member made for a child who has not taken them over go
    --    with the member (recursion), and the link on taken-over ones is cut.
    FOR v_child IN
        SELECT p.account_id FROM mangaly_profile.profile p
         WHERE p.created_by_account_id = p_account AND p.claimed_at IS NULL AND p.account_id <> p_account
        UNION
        SELECT a.id FROM mangaly_identity.account a
         WHERE a.managed_by_account_id = p_account AND a.id <> p_account
           AND NOT EXISTS (SELECT 1 FROM mangaly_identity.account_alias al WHERE al.account_id = a.id)
    LOOP
        v_sub := mangaly_identity.erase_account_data(v_child);
        FOR t IN SELECT jsonb_object_keys(v_sub -> 'deleted') LOOP
            r := mangaly_identity._bump(r, t, (v_sub -> 'deleted' ->> t)::bigint);
        END LOOP;
        FOR t IN SELECT jsonb_array_elements_text(v_sub -> 'file_refs') LOOP v_files := v_files || t; END LOOP;
        FOR t IN SELECT jsonb_array_elements_text(v_sub -> 'dirs') LOOP v_dirs := v_dirs || t; END LOOP;
        r := mangaly_identity._bump(r, 'managed_profiles', 1);
    END LOOP;
    UPDATE mangaly_profile.profile SET created_by_account_id = NULL, updated_at = now()
     WHERE created_by_account_id = p_account;
    -- (the tombstone, not NULL: a taken-over managed account has no phone or
    -- email of its own and 065's CHECK needs one of the three)
    UPDATE mangaly_identity.account SET managed_by_account_id = v_tomb
     WHERE managed_by_account_id = p_account;

    -- 2. Files (collected now, removed from disk by the caller after commit).
    v_dirs := v_dirs || ARRAY(SELECT x::text FROM unnest(v_ids) x);
    SELECT v_files || COALESCE(array_agg(storage_ref), ARRAY[]::text[]) INTO v_files
      FROM mangaly_profile.profile_media WHERE profile_id = ANY (v_ids);
    SELECT v_files || COALESCE(array_agg(storage_ref), ARRAY[]::text[]) INTO v_files
      FROM mangaly_profile.profile_document WHERE profile_id = ANY (v_ids);
    SELECT v_files || COALESCE(array_agg(storage_ref), ARRAY[]::text[]) INTO v_files
      FROM mangaly_trust.evidence_document_ref WHERE profile_id = ANY (v_ids);
    SELECT v_files || COALESCE(array_agg(photo_ref), ARRAY[]::text[]) INTO v_files
      FROM mangaly_profile.member_profile WHERE account_id = p_account AND photo_ref IS NOT NULL;
    SELECT v_files || COALESCE(array_agg(photo_ref), ARRAY[]::text[]) INTO v_files
      FROM mangaly_operations.relationship_manager WHERE account_id = p_account AND photo_ref IS NOT NULL;
    SELECT v_files || COALESCE(array_agg(ref), ARRAY[]::text[]) INTO v_files
      FROM (SELECT unnest(photo_refs) AS ref FROM mangaly_operations.offline_profile WHERE agent_account_id = p_account
            UNION ALL SELECT biodata_ref FROM mangaly_operations.offline_profile
                    WHERE agent_account_id = p_account AND biodata_ref IS NOT NULL) f;
    v_dirs := v_dirs || ARRAY(SELECT 'offline-' || id::text FROM mangaly_operations.offline_profile WHERE agent_account_id = p_account);

    -- 3. Connections, chats, family rows.
    SELECT COALESCE(array_agg(id), ARRAY[]::uuid[]) INTO v_conn
      FROM mangaly_connection.connection_request
     WHERE subject_account_id = p_account OR acting_account_id = p_account
        OR target_profile_id = ANY (v_ids) OR on_behalf_of_profile_id = ANY (v_ids)
        OR decided_by_account_id = p_account;

    SELECT COALESCE(array_agg(DISTINCT cv.id), ARRAY[]::uuid[]) INTO v_conv
      FROM mangaly_communication.conversation cv
     WHERE cv.connection_id = ANY (v_conn)
        OR EXISTS (SELECT 1 FROM mangaly_communication.conversation_participant cp
                    WHERE cp.conversation_id = cv.id AND cp.account_id = p_account);
    -- A thread that would be left with fewer than two people, or that hangs on a
    -- removed connection, is removed whole; a group keeps the others' words.
    DELETE FROM mangaly_communication.message WHERE sender_account_id = p_account;
    GET DIAGNOSTICS n = ROW_COUNT; r := mangaly_identity._bump(r, 'messages', n);
    DELETE FROM mangaly_communication.conversation_participant WHERE account_id = p_account;
    GET DIAGNOSTICS n = ROW_COUNT; r := mangaly_identity._bump(r, 'chat_participations', n);
    DELETE FROM mangaly_safety.detection_signal WHERE conversation_id = ANY (v_conv)
        AND NOT EXISTS (SELECT 1 FROM mangaly_safety.severity_classification sc WHERE sc.detection_signal_id = detection_signal.id);
    DELETE FROM mangaly_communication.conversation cv
     WHERE cv.id = ANY (v_conv)
       AND (cv.connection_id = ANY (v_conn)
            OR (SELECT count(*) FROM mangaly_communication.conversation_participant cp WHERE cp.conversation_id = cv.id) < 2)
       AND NOT EXISTS (SELECT 1 FROM mangaly_communication.legal_hold lh WHERE lh.conversation_id = cv.id AND lh.active);
    GET DIAGNOSTICS n = ROW_COUNT; r := mangaly_identity._bump(r, 'conversations', n);

    DELETE FROM mangaly_connection.connection_request WHERE id = ANY (v_conn);   -- sharing_grant, family_contact_share cascade
    GET DIAGNOSTICS n = ROW_COUNT; r := mangaly_identity._bump(r, 'connection_requests', n);
    DELETE FROM mangaly_connection.family_contact_share
     WHERE candidate_account_id = p_account OR family_member_account_id = p_account;
    GET DIAGNOSTICS n = ROW_COUNT; r := mangaly_identity._bump(r, 'family_contact_shares', n);
    DELETE FROM mangaly_connection.sharing_grant WHERE granted_by_account_id = p_account;
    GET DIAGNOSTICS n = ROW_COUNT; r := mangaly_identity._bump(r, 'sharing_grants', n);
    DELETE FROM mangaly_communication.contact_exchange_request
     WHERE requester_account_id = p_account OR decided_by_account_id = p_account OR connection_id = ANY (v_conn);
    GET DIAGNOSTICS n = ROW_COUNT; r := mangaly_identity._bump(r, 'contact_exchange_requests', n);
    DELETE FROM mangaly_wedding.connection_stage WHERE connection_id = ANY (v_conn) OR updated_by_account_id = p_account;
    GET DIAGNOSTICS n = ROW_COUNT; r := mangaly_identity._bump(r, 'wedding_stages', n);
    DELETE FROM mangaly_lifecycle.meeting_note WHERE noted_by_account_id = p_account OR connection_id = ANY (v_conn);
    GET DIAGNOSTICS n = ROW_COUNT; r := mangaly_identity._bump(r, 'meeting_notes', n);
    DELETE FROM mangaly_lifecycle.success_story_invite
     WHERE invited_by_account_id = p_account OR connection_id = ANY (v_conn);   -- success_story cascades
    GET DIAGNOSTICS n = ROW_COUNT; r := mangaly_identity._bump(r, 'success_story_invites', n);
    DELETE FROM mangaly_lifecycle.profile_lifecycle_status WHERE profile_id = ANY (v_ids);
    GET DIAGNOSTICS n = ROW_COUNT; r := mangaly_identity._bump(r, 'lifecycle_status', n);
    DELETE FROM mangaly_home_circle.connection_home_circle_scope
     WHERE scoped_by_account_id = p_account OR connection_id = ANY (v_conn);
    DELETE FROM mangaly_home_circle.family_introduction
     WHERE side_a_candidate_profile_id = ANY (v_ids) OR side_b_candidate_profile_id = ANY (v_ids) OR connection_id = ANY (v_conn);
    GET DIAGNOSTICS n = ROW_COUNT; r := mangaly_identity._bump(r, 'family_introductions', n);

    -- 4. Home Circle (a member's circle, and circles the member sits in).
    SELECT COALESCE(array_agg(id), ARRAY[]::uuid[]) INTO v_mem
      FROM mangaly_home_circle.membership
     WHERE member_account_id = p_account OR candidate_profile_id = ANY (v_ids);
    -- reports about circle members stay, pseudonymised
    UPDATE mangaly_home_circle.report SET reporter_account_id = v_tomb, reason = '[removed]'
     WHERE reporter_account_id = p_account;
    GET DIAGNOSTICS n = ROW_COUNT; k := mangaly_identity._bump(k, 'home_circle_reports', n);
    UPDATE mangaly_home_circle.membership m
       SET member_account_id = CASE WHEN m.member_account_id = p_account THEN v_tomb ELSE m.member_account_id END,
           candidate_profile_id = CASE WHEN m.candidate_profile_id = ANY (v_ids) THEN v_tomb ELSE m.candidate_profile_id END,
           status = 'removed', removed_at = COALESCE(m.removed_at, now()), updated_at = now()
     WHERE m.id = ANY (v_mem)
       AND EXISTS (SELECT 1 FROM mangaly_home_circle.report rp WHERE rp.membership_id = m.id);
    DELETE FROM mangaly_home_circle.home_circle_note
     WHERE candidate_profile_id = ANY (v_ids) OR subject_account_id = p_account OR author_membership_id = ANY (v_mem);
    GET DIAGNOSTICS n = ROW_COUNT; r := mangaly_identity._bump(r, 'home_circle_notes', n);
    DELETE FROM mangaly_home_circle.discovery_hint
     WHERE candidate_profile_id = ANY (v_ids) OR submitted_by_membership_id = ANY (v_mem);
    GET DIAGNOSTICS n = ROW_COUNT; r := mangaly_identity._bump(r, 'home_circle_hints', n);
    DELETE FROM mangaly_home_circle.suggestion
     WHERE candidate_profile_id = ANY (v_ids) OR suggested_profile_id = ANY (v_ids) OR suggested_by_membership_id = ANY (v_mem);
    GET DIAGNOSTICS n = ROW_COUNT; r := mangaly_identity._bump(r, 'home_circle_suggestions', n);
    DELETE FROM mangaly_home_circle.membership m
     WHERE m.id = ANY (v_mem) AND NOT EXISTS (SELECT 1 FROM mangaly_home_circle.report rp WHERE rp.membership_id = m.id);
    GET DIAGNOSTICS n = ROW_COUNT; r := mangaly_identity._bump(r, 'home_circle_memberships', n);
    DELETE FROM mangaly_home_circle.invitation
     WHERE candidate_profile_id = ANY (v_ids) OR inviter_account_id = p_account OR invitee_account_id = p_account
        OR (invitee_identifier IS NOT NULL AND invitee_identifier IN (COALESCE(v_phone, '-'), COALESCE(v_email, '-')));
    GET DIAGNOSTICS n = ROW_COUNT; r := mangaly_identity._bump(r, 'home_circle_invitations', n);

    -- 5. Profile, attributes, photos, documents, discovery, matching.
    DELETE FROM mangaly_profile.profile WHERE id = ANY (v_prof);   -- attributes, media, documents cascade
    GET DIAGNOSTICS n = ROW_COUNT; r := mangaly_identity._bump(r, 'profiles', n);
    DELETE FROM mangaly_profile.member_profile WHERE account_id = p_account;
    GET DIAGNOSTICS n = ROW_COUNT; r := mangaly_identity._bump(r, 'member_profiles', n);
    DELETE FROM mangaly_profile.profile_view WHERE viewer_account_id = p_account OR viewed_account_id = p_account;
    GET DIAGNOSTICS n = ROW_COUNT; r := mangaly_identity._bump(r, 'profile_views', n);
    DELETE FROM mangaly_discovery.discovery_profile_index WHERE profile_id = ANY (v_ids);
    GET DIAGNOSTICS n = ROW_COUNT; r := mangaly_identity._bump(r, 'discovery_index', n);
    DELETE FROM mangaly_discovery.shortlist
     WHERE candidate_account_id = p_account OR saved_by_account_id = p_account OR saved_account_id = p_account;
    GET DIAGNOSTICS n = ROW_COUNT; r := mangaly_identity._bump(r, 'shortlist', n);
    DELETE FROM mangaly_discovery.daily_pick WHERE account_id = p_account OR pick_account_id = p_account;
    GET DIAGNOSTICS n = ROW_COUNT; r := mangaly_identity._bump(r, 'daily_picks', n);
    DELETE FROM mangaly_compatibility.assessment_response WHERE profile_id = ANY (v_ids);
    GET DIAGNOSTICS n = ROW_COUNT; r := mangaly_identity._bump(r, 'assessment_responses', n);
    DELETE FROM mangaly_compatibility.horoscope WHERE profile_id = ANY (v_ids);
    GET DIAGNOSTICS n = ROW_COUNT; r := mangaly_identity._bump(r, 'horoscope_birth_details', n);
    DELETE FROM mangaly_horoscope.chart WHERE account_id = p_account;
    GET DIAGNOSTICS n = ROW_COUNT; r := mangaly_identity._bump(r, 'horoscope_charts', n);
    DELETE FROM mangaly_horoscope.match WHERE groom_account_id = p_account OR bride_account_id = p_account;
    GET DIAGNOSTICS n = ROW_COUNT; r := mangaly_identity._bump(r, 'horoscope_matches', n);

    -- 6. Trust layer.
    DELETE FROM mangaly_trust.evidence_document_ref WHERE profile_id = ANY (v_ids);
    GET DIAGNOSTICS n = ROW_COUNT; r := mangaly_identity._bump(r, 'verification_evidence', n);
    DELETE FROM mangaly_trust.admin_verification_request WHERE profile_id = ANY (v_ids);
    DELETE FROM mangaly_trust.verification_circle_invite WHERE profile_id = ANY (v_ids) OR verifier_account_id = p_account;
    GET DIAGNOSTICS n = ROW_COUNT; r := mangaly_identity._bump(r, 'verification_invites', n);
    DELETE FROM mangaly_trust.verification_layer_status WHERE profile_id = ANY (v_ids);
    GET DIAGNOSTICS n = ROW_COUNT; r := mangaly_identity._bump(r, 'verification_layers', n);
    DELETE FROM mangaly_trust.member_face_match WHERE account_id = p_account;
    GET DIAGNOSTICS n = ROW_COUNT; r := mangaly_identity._bump(r, 'face_match', n);
    DELETE FROM mangaly_trust.biometric_consent WHERE account_id = p_account;
    GET DIAGNOSTICS n = ROW_COUNT; r := mangaly_identity._bump(r, 'biometric_consents', n);

    -- 7. Access grants, blocks.
    DELETE FROM mangaly_authz."grant" WHERE subject_id = p_account OR target_profile_id = ANY (v_ids);
    GET DIAGNOSTICS n = ROW_COUNT; r := mangaly_identity._bump(r, 'access_grants', n);
    DELETE FROM mangaly_safety.block WHERE blocker_account_id = p_account OR blocked_account_id = p_account;
    GET DIAGNOSTICS n = ROW_COUNT; r := mangaly_identity._bump(r, 'blocks', n);

    -- 8. Agent (broker) data: the agent profile and offline clients go; the
    --    clients' own accounts are untouched (only the assignment row is removed).
    DELETE FROM mangaly_operations.rm_suggestion WHERE suggested_account_id = p_account
        OR offline_profile_id IN (SELECT id FROM mangaly_operations.offline_profile WHERE agent_account_id = p_account);
    DELETE FROM mangaly_operations.rm_assignment WHERE rm_account_id = p_account OR member_account_id = p_account;
    GET DIAGNOSTICS n = ROW_COUNT; r := mangaly_identity._bump(r, 'agent_client_links', n);
    DELETE FROM mangaly_operations.offline_profile WHERE agent_account_id = p_account;
    GET DIAGNOSTICS n = ROW_COUNT; r := mangaly_identity._bump(r, 'offline_client_profiles', n);
    DELETE FROM mangaly_operations.relationship_manager WHERE account_id = p_account;
    GET DIAGNOSTICS n = ROW_COUNT; r := mangaly_identity._bump(r, 'agent_profiles', n);
    DELETE FROM mangaly_operations.agent_contact_view WHERE agent_account_id = p_account OR member_account_id = p_account;
    GET DIAGNOSTICS n = ROW_COUNT; r := mangaly_identity._bump(r, 'agent_contact_views', n);
    DELETE FROM mangaly_operations.agent_export WHERE agent_account_id = p_account;
    GET DIAGNOSTICS n = ROW_COUNT; r := mangaly_identity._bump(r, 'agent_exports', n);
    UPDATE mangaly_operations.agent_export SET member_ids = array_remove(member_ids, p_account)
     WHERE p_account = ANY (member_ids);
    DELETE FROM mangaly_operations.support_ticket WHERE submitted_by_account_id = p_account;
    GET DIAGNOSTICS n = ROW_COUNT; r := mangaly_identity._bump(r, 'support_tickets', n);

    -- 9. Retained, pseudonymised: reports, cases, suspensions, appeals.
    UPDATE mangaly_safety.report SET reporter_account_id = CASE WHEN reporter_account_id = p_account THEN v_tomb ELSE reporter_account_id END,
           reported_profile_id = CASE WHEN reported_profile_id = ANY (v_ids) THEN v_tomb ELSE reported_profile_id END,
           description = NULL, evidence = NULL, meeting_context_reference = NULL,
           reported_message_id = NULL, reported_conversation_id = NULL
     WHERE reporter_account_id = p_account OR reported_profile_id = ANY (v_ids);
    GET DIAGNOSTICS n = ROW_COUNT; k := mangaly_identity._bump(k, 'safety_reports', n);
    UPDATE mangaly_operations.contact_report SET
           member_account_id = CASE WHEN member_account_id = p_account THEN v_tomb ELSE member_account_id END,
           reported_by = CASE WHEN reported_by = p_account THEN v_tomb ELSE reported_by END,
           named_agent_id = CASE WHEN named_agent_id = p_account THEN v_tomb ELSE named_agent_id END,
           suspect_agent_ids = array_replace(suspect_agent_ids, p_account, v_tomb), note = NULL
     WHERE member_account_id = p_account OR reported_by = p_account OR named_agent_id = p_account OR p_account = ANY (suspect_agent_ids);
    GET DIAGNOSTICS n = ROW_COUNT; k := mangaly_identity._bump(k, 'contact_reports', n);
    UPDATE mangaly_operations.account_suspension SET account_id = v_tomb, reason = NULL,
           suspended_by = CASE WHEN suspended_by = p_account THEN v_tomb ELSE suspended_by END
     WHERE account_id = p_account;
    GET DIAGNOSTICS n = ROW_COUNT; k := mangaly_identity._bump(k, 'suspensions', n);
    UPDATE mangaly_operations.case_appeal SET appealed_by_account_id = v_tomb WHERE appealed_by_account_id = p_account;
    GET DIAGNOSTICS n = ROW_COUNT; k := mangaly_identity._bump(k, 'case_appeals', n);

    -- 10. Billing: sandbox / unpaid orders go; real paid money is retained
    --     (tax law) with the tombstone only.
    DELETE FROM mangaly_billing.plan_subscription ps
     WHERE ps.account_id = p_account
       AND (ps.order_id IS NULL OR NOT EXISTS (SELECT 1 FROM mangaly_billing."order" o
                                                WHERE o.id = ps.order_id AND o.status = 'paid' AND o.gateway NOT IN ('dev-sandbox', 'sandbox')));
    GET DIAGNOSTICS n = ROW_COUNT; r := mangaly_identity._bump(r, 'plan_subscriptions', n);
    DELETE FROM mangaly_billing."order" o
     WHERE o.account_id = p_account AND NOT (o.status = 'paid' AND o.gateway NOT IN ('dev-sandbox', 'sandbox'));
    GET DIAGNOSTICS n = ROW_COUNT; r := mangaly_identity._bump(r, 'billing_orders', n);
    UPDATE mangaly_billing."order" SET account_id = v_tomb, gateway_order_id = gateway_order_id WHERE account_id = p_account;
    GET DIAGNOSTICS n = ROW_COUNT; k := mangaly_identity._bump(k, 'paid_orders', n);
    UPDATE mangaly_billing.plan_subscription SET account_id = v_tomb WHERE account_id = p_account;

    -- 11. Notifications, idempotency, rate limits, event outbox.
    DELETE FROM mangaly_notification.inbox_entry
     WHERE recipient_account_id = p_account OR subject_account_id = p_account;
    GET DIAGNOSTICS n = ROW_COUNT; r := mangaly_identity._bump(r, 'notifications', n);
    DELETE FROM mangaly_platform.idempotency_key WHERE account_id = p_account;
    GET DIAGNOSTICS n = ROW_COUNT; r := mangaly_identity._bump(r, 'idempotency_keys', n);
    -- keys are '<scope>:<sha256 of the lower-cased subject>' (see rate_limiting/limiter.py)
    DELETE FROM mangaly_platform.rate_limit_counter
     WHERE rate_limit_key NOT LIKE 'delete_account_data:%'   -- keeps the 3-an-hour limit meaningful
       AND (rate_limit_key ~* v_re
        OR split_part(rate_limit_key, ':', 2) IN (
             SELECT encode(sha256(convert_to(lower(btrim(x)), 'UTF8')), 'hex')
               FROM unnest(ARRAY(SELECT i::text FROM unnest(v_ids) i) || ARRAY[v_phone, v_email]) x
              WHERE x IS NOT NULL));
    GET DIAGNOSTICS n = ROW_COUNT; r := mangaly_identity._bump(r, 'rate_limit_counters', n);
    FOR t IN SELECT format('%I.outbox_event', schemaname)
               FROM (SELECT DISTINCT table_schema AS schemaname FROM information_schema.tables
                      WHERE table_schema LIKE 'mangaly\_%' AND table_name = 'outbox_event') s LOOP
        EXECUTE format('DELETE FROM %s WHERE aggregate_id = ANY ($1) OR payload::text ~* $2', t) USING v_ids, v_re;
        GET DIAGNOSTICS n = ROW_COUNT; r := mangaly_identity._bump(r, 'outbox_events', n);
    END LOOP;

    -- 12. Sign-in rows last: sessions, one-time codes, the account itself.
    DELETE FROM mangaly_identity.session WHERE account_id = p_account;
    GET DIAGNOSTICS n = ROW_COUNT; r := mangaly_identity._bump(r, 'sessions', n);
    DELETE FROM mangaly_identity.otp_challenge WHERE account_id = p_account;
    DELETE FROM mangaly_identity.password_reset_token WHERE account_id = p_account;
    DELETE FROM mangaly_identity.account_alias WHERE account_id = p_account OR member_id = p_account;
    GET DIAGNOSTICS n = ROW_COUNT; r := mangaly_identity._bump(r, 'account_links', n);
    DELETE FROM mangaly_identity.account WHERE id = p_account;
    GET DIAGNOSTICS n = ROW_COUNT; r := mangaly_identity._bump(r, 'accounts', n);

    INSERT INTO mangaly_platform.deletion_receipt (tombstone, counts)
    VALUES (v_tomb::text, jsonb_build_object('deleted', r, 'retained', k));

    RETURN jsonb_build_object('status', 'done', 'deleted', r, 'retained', k,
                              'file_refs', to_jsonb(v_files), 'dirs', to_jsonb(v_dirs));
END;
$$;
REVOKE ALL ON FUNCTION mangaly_identity.erase_account_data(uuid) FROM PUBLIC;

-- Member-facing: only the signed-in account, no argument to aim elsewhere.
CREATE OR REPLACE FUNCTION mangaly_identity.erase_my_data()
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = mangaly_identity, pg_temp
AS $$
DECLARE
    v_me uuid := NULLIF(current_setting('mangaly.account_id', true), '')::uuid;
BEGIN
    IF v_me IS NULL THEN
        RAISE EXCEPTION 'erase_my_data: not signed in' USING ERRCODE = '28000';
    END IF;
    RETURN mangaly_identity.erase_account_data(v_me);
END;
$$;
REVOKE ALL ON FUNCTION mangaly_identity.erase_my_data() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_identity.erase_my_data() TO mangaly_app;

-- Platform-facing (internal endpoint): a ForKhatri member id -> its Mangalya account(s).
CREATE OR REPLACE FUNCTION mangaly_identity.erase_member_data(p_member uuid)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = mangaly_identity, pg_temp
AS $$
DECLARE
    v_acc uuid;
    v_out jsonb := jsonb_build_object('status', 'nothing_to_delete', 'deleted', '{}'::jsonb,
                                      'retained', '{}'::jsonb, 'file_refs', '[]'::jsonb, 'dirs', '[]'::jsonb);
    v_one jsonb;
    t text;
BEGIN
    FOR v_acc IN
        SELECT DISTINCT x FROM (VALUES (p_member), (mangaly_identity.alias_of(p_member))) v(x) WHERE x IS NOT NULL
    LOOP
        v_one := mangaly_identity.erase_account_data(v_acc);
        IF v_one ->> 'status' = 'done' THEN
            v_out := jsonb_set(v_out, '{status}', '"done"');
            FOR t IN SELECT jsonb_object_keys(v_one -> 'deleted') LOOP
                v_out := jsonb_set(v_out, ARRAY['deleted', t],
                    to_jsonb(COALESCE((v_out -> 'deleted' ->> t)::bigint, 0) + (v_one -> 'deleted' ->> t)::bigint));
            END LOOP;
            FOR t IN SELECT jsonb_object_keys(v_one -> 'retained') LOOP
                v_out := jsonb_set(v_out, ARRAY['retained', t],
                    to_jsonb(COALESCE((v_out -> 'retained' ->> t)::bigint, 0) + (v_one -> 'retained' ->> t)::bigint));
            END LOOP;
            v_out := jsonb_set(v_out, '{file_refs}', (v_out -> 'file_refs') || (v_one -> 'file_refs'));
            v_out := jsonb_set(v_out, '{dirs}', (v_out -> 'dirs') || (v_one -> 'dirs'));
        END IF;
    END LOOP;
    RETURN v_out;
END;
$$;
REVOKE ALL ON FUNCTION mangaly_identity.erase_member_data(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_identity.erase_member_data(uuid) TO mangaly_app;
