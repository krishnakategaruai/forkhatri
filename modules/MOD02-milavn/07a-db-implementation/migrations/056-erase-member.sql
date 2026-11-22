-- 056: erase one member's data from Milavn (ACCOUNT-DELETION contract, kinds A and B).
-- Additive and safe to re-run. No existing table, policy or function is changed.
--
--   milavn_platform.tombstone(uuid)           one-way stand-in id for a deleted member ('dead0000-...').
--   milavn_platform.erasure_receipt           one line per erasure (tombstone, date, counts): proof it was done.
--   milavn_platform.erase_member(uuid, text[]) the whole erase, one transaction, idempotent. Returns jsonb:
--        {deleted:{kind:n}, pseudonymised:{kind:n}, files:[refs], retained:[{kind,reason}]}
--
-- SECURITY DEFINER owned by milavn_owner (the owner is not subject to row level security, no policy is loosened).
-- It acts only when the caller is that member (milavn.member_id) or the internal service (milavn.internal_service),
-- the same gates the other definer functions use. The service removes the listed files from disk after commit.

CREATE TABLE IF NOT EXISTS milavn_platform.erasure_receipt (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tombstone uuid NOT NULL,
  erased_at timestamptz NOT NULL DEFAULT now(),
  deleted jsonb NOT NULL,
  pseudonymised jsonb NOT NULL
);
COMMENT ON TABLE milavn_platform.erasure_receipt IS 'Deletion receipts: tombstone id, date and counts only. No name, contact or text.';

CREATE OR REPLACE FUNCTION milavn_platform.tombstone(p_member uuid)
RETURNS uuid LANGUAGE sql IMMUTABLE
SET search_path = pg_catalog AS $$
  SELECT ('dead0000' || substr(encode(sha256(convert_to('forkhatri-erased:' || p_member::text, 'UTF8')), 'hex'), 1, 24))::uuid
$$;

CREATE OR REPLACE FUNCTION milavn_platform.erase_member(p_member uuid, p_names text[] DEFAULT '{}')
RETURNS jsonb
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = milavn_platform, milavn_profile, milavn_activity, milavn_circle, milavn_connect, milavn_notification,
                  milavn_safety, milavn_trust, milavn_ticketing, milavn_locationprivacy, milavn_discovery, pg_catalog AS $$
DECLARE
  T uuid := milavn_platform.tombstone(p_member);
  who text := current_setting('milavn.member_id', true);
  internal text := current_setting('milavn.internal_service', true);
  del jsonb := '{}'::jsonb;
  pse jsonb := '{}'::jsonb;
  refs text[] := '{}';
  r text[];
  n int;
  v record;
  c record;
  nxt uuid;
  guard int;
  nm text;
  retained jsonb := '[]'::jsonb;
  total int;
BEGIN
  IF p_member IS NULL OR p_member = '00000000-0000-0000-0000-000000000000'::uuid THEN
    RAISE EXCEPTION 'erase_member: no member' USING ERRCODE = '22023';
  END IF;
  IF NOT (who = p_member::text OR internal = 'true') THEN
    RAISE EXCEPTION 'erase_member: not allowed' USING ERRCODE = '42501';
  END IF;
  PERFORM pg_advisory_xact_lock(hashtext('milavn-erase:' || p_member::text));

  -- 1. Events the member hosts. Upcoming ones still active are cancelled (the service already cancelled them
  --    with refunds and attendee notices; this is the safety net). Every event stays, hosted by the tombstone,
  --    with its contact details removed.
  UPDATE occurrence SET status = 'cancelled', cancelled_at = now(), updated_at = now()
   WHERE creator_member_id = p_member AND status = 'active' AND coalesce(time_end, time_start) > now();
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n > 0 THEN del := del || jsonb_build_object('events_cancelled', n); END IF;
  DELETE FROM occurrence_contact WHERE occurrence_id IN (SELECT id FROM occurrence WHERE creator_member_id = p_member);
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n > 0 THEN del := del || jsonb_build_object('event_contacts', n); END IF;
  UPDATE occurrence SET creator_member_id = T WHERE creator_member_id = p_member;
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n > 0 THEN pse := pse || jsonb_build_object('events_hosted', n); END IF;
  UPDATE activity SET creator_member_id = T WHERE creator_member_id = p_member;

  -- 2. Participation: leave every team, free the spot (next on the waitlist moves up on free events), then delete.
  UPDATE qr_checkin_token SET used_by_participation_id = NULL
   WHERE used_by_participation_id IN (SELECT id FROM participation WHERE member_id = p_member);
  FOR v IN SELECT team_id FROM event_team_member WHERE member_id = p_member LOOP
    PERFORM milavn_activity.team_drop_member(v.team_id, p_member);
  END LOOP;
  CREATE TEMP TABLE IF NOT EXISTS _erase_freed (occurrence_id uuid) ON COMMIT DROP;
  TRUNCATE _erase_freed;
  INSERT INTO _erase_freed
    SELECT p.occurrence_id FROM participation p JOIN occurrence o ON o.id = p.occurrence_id
     WHERE p.member_id = p_member AND p.status IN ('going', 'checked_in') AND o.status = 'active'
       AND coalesce(o.time_end, o.time_start) > now() AND o.price_paise IS NULL;
  DELETE FROM participation WHERE member_id = p_member;
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n > 0 THEN del := del || jsonb_build_object('participations', n); END IF;
  FOR v IN SELECT f.occurrence_id, o.capacity FROM _erase_freed f JOIN occurrence o ON o.id = f.occurrence_id LOOP
    guard := 0;
    WHILE guard < 20 AND (v.capacity IS NULL OR milavn_activity.going_count(v.occurrence_id) < v.capacity) LOOP
      PERFORM 1 FROM milavn_activity.promote_next_waitlisted(v.occurrence_id, p_member);
      EXIT WHEN NOT FOUND;
      guard := guard + 1;
    END LOOP;
  END LOOP;
  UPDATE participation_status_history SET changed_by_member_id = T WHERE changed_by_member_id = p_member;
  DELETE FROM event_team_member WHERE member_id = p_member;
  DELETE FROM occurrence_co_organizer WHERE member_id = p_member;
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n > 0 THEN del := del || jsonb_build_object('co_organizer_roles', n); END IF;
  UPDATE occurrence_co_organizer SET granted_by_member_id = T WHERE granted_by_member_id = p_member;
  UPDATE occurrence_cohost SET invited_by_member_id = T WHERE invited_by_member_id = p_member;
  UPDATE occurrence_cohost SET decided_by_member_id = T WHERE decided_by_member_id = p_member;
  DELETE FROM event_speaker WHERE member_id = p_member;
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n > 0 THEN del := del || jsonb_build_object('event_speaker_entries', n); END IF;
  DELETE FROM occurrence_message WHERE member_id = p_member;
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n > 0 THEN del := del || jsonb_build_object('event_thread_messages', n); END IF;
  DELETE FROM occurrence_update WHERE organizer_member_id = p_member;
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n > 0 THEN del := del || jsonb_build_object('event_announcements', n); END IF;
  WITH d AS (DELETE FROM occurrence_photo WHERE member_id = p_member RETURNING storage_ref)
    SELECT count(*), coalesce(array_agg(storage_ref) FILTER (WHERE storage_ref IS NOT NULL), '{}') INTO n, r FROM d;
  IF n > 0 THEN del := del || jsonb_build_object('moment_photos', n); refs := refs || r; END IF;
  UPDATE occurrence_photo SET removal_requested_by = NULL WHERE removal_requested_by = p_member;
  DELETE FROM calendar_follow WHERE member_id = p_member OR host_member_id = p_member;
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n > 0 THEN del := del || jsonb_build_object('calendar_follows', n); END IF;
  DELETE FROM series_regular WHERE member_id = p_member;
  DELETE FROM photo_preference WHERE member_id = p_member;
  DELETE FROM milavn_discovery.hidden_occurrence WHERE member_id = p_member OR host_member_id = p_member;
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n > 0 THEN del := del || jsonb_build_object('hidden_events', n); END IF;

  -- 3. Tickets: where money moved the row stays as a payment record under the tombstone (no QR, no pay link);
  --    holds and unpaid tickets are deleted.
  DELETE FROM ticket WHERE member_id = p_member AND status NOT IN ('paid', 'refund_pending', 'refunded');
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n > 0 THEN del := del || jsonb_build_object('tickets_unpaid', n); END IF;
  UPDATE ticket SET member_id = T, qr_code = NULL, checkout_url = NULL, updated_at = now() WHERE member_id = p_member;
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n > 0 THEN
    pse := pse || jsonb_build_object('payment_records', n);
    retained := retained || jsonb_build_object('kind', 'payment_records', 'reason', 'Tickets that were paid or refunded stay as payment records for legal and tax retention, under a one-way deletion id with amount and date only.');
  END IF;

  -- 4. Circles: a circle the member organises passes to the longest-standing other organiser or assistant;
  --    with nobody to take it over, the circle is deleted (its posts, photos and files with it).
  FOR c IN SELECT circle_id FROM circle_membership WHERE member_id = p_member AND member_role = 'organizer' AND left_at IS NULL LOOP
    SELECT m.member_id INTO nxt FROM circle_membership m
     WHERE m.circle_id = c.circle_id AND m.member_id <> p_member AND m.left_at IS NULL AND m.member_role IN ('organizer', 'assistant')
     ORDER BY (m.member_role = 'organizer') DESC, m.joined_at LIMIT 1;
    IF nxt IS NULL THEN
      SELECT coalesce(array_agg(x) FILTER (WHERE x IS NOT NULL), '{}') INTO r FROM (
        SELECT cover_ref AS x FROM circle WHERE id = c.circle_id
        UNION ALL SELECT photo_ref FROM circle_post WHERE circle_id = c.circle_id
        UNION ALL SELECT storage_ref FROM circle_post_media WHERE circle_id = c.circle_id
        UNION ALL SELECT storage_ref FROM circle_album_photo WHERE circle_id = c.circle_id) s;
      refs := refs || r;
      UPDATE circle_formation_suggestion SET created_circle_id = NULL WHERE created_circle_id = c.circle_id;
      UPDATE occurrence SET circle_id = NULL WHERE circle_id = c.circle_id;
      DELETE FROM circle WHERE id = c.circle_id;
      del := jsonb_set(del, '{circles_deleted}', to_jsonb(coalesce((del->>'circles_deleted')::int, 0) + 1));
    ELSE
      UPDATE circle_membership SET member_role = 'organizer' WHERE circle_id = c.circle_id AND member_id = nxt;
      UPDATE circle SET created_by_member_id = nxt WHERE id = c.circle_id AND created_by_member_id = p_member;
      pse := jsonb_set(pse, '{circles_handed_over}', to_jsonb(coalesce((pse->>'circles_handed_over')::int, 0) + 1));
    END IF;
  END LOOP;
  UPDATE circle SET created_by_member_id = T WHERE created_by_member_id = p_member;

  WITH d AS (DELETE FROM circle_post_media WHERE post_id IN (SELECT id FROM circle_post WHERE member_id = p_member) RETURNING storage_ref)
    SELECT coalesce(array_agg(storage_ref) FILTER (WHERE storage_ref IS NOT NULL), '{}') INTO r FROM d;
  refs := refs || r;
  WITH d AS (DELETE FROM circle_post WHERE member_id = p_member RETURNING photo_ref)
    SELECT count(*), coalesce(array_agg(photo_ref) FILTER (WHERE photo_ref IS NOT NULL), '{}') INTO n, r FROM d;
  IF n > 0 THEN del := del || jsonb_build_object('circle_posts', n); refs := refs || r; END IF;
  DELETE FROM circle_post_comment WHERE member_id = p_member;
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n > 0 THEN del := del || jsonb_build_object('circle_comments', n); END IF;
  DELETE FROM circle_post_reaction WHERE member_id = p_member;
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n > 0 THEN del := del || jsonb_build_object('circle_reactions', n); END IF;
  WITH d AS (DELETE FROM circle_album_photo WHERE member_id = p_member RETURNING storage_ref)
    SELECT count(*), coalesce(array_agg(storage_ref) FILTER (WHERE storage_ref IS NOT NULL), '{}') INTO n, r FROM d;
  IF n > 0 THEN del := del || jsonb_build_object('album_photos', n); refs := refs || r; END IF;
  UPDATE circle_album SET created_by_member_id = T WHERE created_by_member_id = p_member;
  DELETE FROM poll_vote WHERE member_id = p_member;
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n > 0 THEN del := del || jsonb_build_object('poll_votes', n); END IF;
  UPDATE poll SET created_by_member_id = T WHERE created_by_member_id = p_member;
  DELETE FROM fundraiser_pledge WHERE member_id = p_member AND paid_at IS NULL;
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n > 0 THEN del := del || jsonb_build_object('pledges_unpaid', n); END IF;
  UPDATE fundraiser_pledge SET member_id = T, note = NULL WHERE member_id = p_member;
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n > 0 THEN
    pse := pse || jsonb_build_object('paid_pledges', n);
    retained := retained || jsonb_build_object('kind', 'payment_records', 'reason', 'Paid pledges stay as payment records for legal and tax retention, under a one-way deletion id with amount and date only.');
  END IF;
  UPDATE fundraiser SET created_by_member_id = T WHERE created_by_member_id = p_member;
  DELETE FROM circle_group_update WHERE created_by_member_id = p_member;
  UPDATE circle_group SET created_by_member_id = T WHERE created_by_member_id = p_member;
  DELETE FROM circle_formation_suggestion_member WHERE member_id = p_member;
  DELETE FROM circle_invite WHERE invited_member_id = p_member;
  UPDATE circle_invite SET invited_by_member_id = T WHERE invited_by_member_id = p_member;
  DELETE FROM circle_invite_link WHERE created_by_member_id = p_member;
  DELETE FROM join_request WHERE member_id = p_member;
  UPDATE join_request SET decided_by_member_id = T WHERE decided_by_member_id = p_member;
  DELETE FROM circle_notify_setting WHERE member_id = p_member;
  DELETE FROM circle_membership WHERE member_id = p_member;
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n > 0 THEN del := del || jsonb_build_object('circle_memberships', n); END IF;
  UPDATE organization_scope SET created_by_member_id = T WHERE created_by_member_id = p_member;

  -- 5. Chat: the member's messages and photos are deleted. A one-to-one chat stays for the other person with the
  --    tombstone in the member's place ("Deleted member"); chats nobody else remains in are deleted.
  CREATE TEMP TABLE IF NOT EXISTS _erase_conv (id uuid) ON COMMIT DROP;
  TRUNCATE _erase_conv;
  INSERT INTO _erase_conv SELECT conversation_id FROM conversation_member WHERE member_id = p_member
    UNION SELECT id FROM conversation WHERE created_by = p_member;
  WITH d AS (DELETE FROM chat_message WHERE member_id = p_member RETURNING media_ref)
    SELECT count(*), coalesce(array_agg(media_ref) FILTER (WHERE media_ref IS NOT NULL), '{}') INTO n, r FROM d;
  IF n > 0 THEN del := del || jsonb_build_object('chat_messages', n); refs := refs || r; END IF;
  DELETE FROM message_reaction WHERE member_id = p_member;
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n > 0 THEN del := del || jsonb_build_object('chat_reactions', n); END IF;
  UPDATE conversation_member cm SET member_id = T, last_read_at = NULL, muted = false
   WHERE cm.member_id = p_member AND EXISTS (SELECT 1 FROM conversation cv WHERE cv.id = cm.conversation_id AND cv.kind = 'direct');
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n > 0 THEN pse := pse || jsonb_build_object('direct_chats_kept_for_other_person', n); END IF;
  DELETE FROM conversation_member WHERE member_id = p_member;
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n > 0 THEN del := del || jsonb_build_object('chat_memberships', n); END IF;
  UPDATE conversation SET created_by = T WHERE created_by = p_member;
  WITH gone AS (
    SELECT e.id FROM _erase_conv e
     WHERE NOT EXISTS (SELECT 1 FROM conversation_member m WHERE m.conversation_id = e.id AND m.member_id <> T AND m.left_at IS NULL)),
  pics AS (SELECT coalesce(array_agg(media_ref) FILTER (WHERE media_ref IS NOT NULL), '{}') AS pr FROM chat_message WHERE conversation_id IN (SELECT id FROM gone)),
  d AS (DELETE FROM conversation WHERE id IN (SELECT id FROM gone) RETURNING id)
  SELECT (SELECT count(*) FROM d), (SELECT pr FROM pics) INTO n, r;
  IF n > 0 THEN del := del || jsonb_build_object('chats_deleted', n); refs := refs || r; END IF;
  DELETE FROM free_now WHERE member_id = p_member;
  DELETE FROM presence WHERE member_id = p_member;
  DELETE FROM meet_again WHERE chooser_member_id = p_member OR chosen_member_id = p_member;
  DELETE FROM meet_again_told WHERE low_member_id = p_member OR high_member_id = p_member;

  -- 6. Trust and safety. The member's own feedback, reputation and thanks are deleted. Reports and blocks that
  --    involve the member stay only as a minimal safety record under the tombstone, free text removed.
  DELETE FROM feedback WHERE participant_member_id = p_member;
  DELETE FROM reputation_signal WHERE member_id = p_member;
  DELETE FROM thanks WHERE from_member_id = p_member OR to_member_id = p_member;
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n > 0 THEN del := del || jsonb_build_object('thanks', n); END IF;
  DELETE FROM block WHERE blocking_member_id = p_member;
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n > 0 THEN del := del || jsonb_build_object('blocks_made', n); END IF;
  UPDATE report SET reporter_member_id = T, description = '' WHERE reporter_member_id = p_member;
  GET DIAGNOSTICS n = ROW_COUNT;
  UPDATE report SET subject_id = T, description = '' WHERE subject_type = 'user' AND subject_id = p_member;
  GET DIAGNOSTICS guard = ROW_COUNT;
  UPDATE block SET blocked_member_id = T WHERE blocked_member_id = p_member;
  UPDATE moderation_action SET moderator_member_id = T WHERE moderator_member_id = p_member;
  UPDATE trust_status SET subject_id = T WHERE subject_type = 'organizer' AND subject_id = p_member;
  IF n + guard > 0 THEN
    pse := pse || jsonb_build_object('reports', n + guard);
    retained := retained || jsonb_build_object('kind', 'safety_records', 'reason', 'A report filed by or about the member, and blocks against the member, stay so that a deleted member cannot simply return and harm others. Only a one-way deletion id, the reason category and the status are kept; no name, contact or text.');
  END IF;
  UPDATE ranking_weight_config SET created_by_member_id = T WHERE created_by_member_id = p_member;

  -- 7. Notifications, queues, settings and the profile itself.
  DELETE FROM notification_inbox_entry WHERE member_id = p_member;
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n > 0 THEN del := del || jsonb_build_object('notifications', n); END IF;
  DELETE FROM notification_outbox WHERE member_id = p_member;
  DELETE FROM notification_preference WHERE member_id = p_member;
  DELETE FROM reminder_sent WHERE member_id = p_member;
  -- the member's name inside other people's notices
  FOREACH nm IN ARRAY p_names LOOP
    IF length(trim(nm)) >= 3 THEN
      UPDATE notification_inbox_entry SET title = replace(title, nm, 'A deleted member'), body = replace(body, nm, 'A deleted member')
       WHERE title LIKE '%' || nm || '%' OR body LIKE '%' || nm || '%';
    END IF;
  END LOOP;
  -- the member's id inside queued events and replayed requests
  UPDATE notification_outbox SET payload = replace(payload::text, p_member::text, T::text)::jsonb WHERE payload::text LIKE '%' || p_member::text || '%';
  UPDATE milavn_activity.outbox_event SET payload = replace(payload::text, p_member::text, T::text)::jsonb WHERE payload::text LIKE '%' || p_member::text || '%';
  UPDATE milavn_circle.outbox_event SET payload = replace(payload::text, p_member::text, T::text)::jsonb WHERE payload::text LIKE '%' || p_member::text || '%';
  UPDATE milavn_safety.outbox_event SET payload = replace(payload::text, p_member::text, T::text)::jsonb WHERE payload::text LIKE '%' || p_member::text || '%';
  UPDATE milavn_trust.outbox_event SET payload = replace(payload::text, p_member::text, T::text)::jsonb WHERE payload::text LIKE '%' || p_member::text || '%';
  DELETE FROM idempotency_key WHERE actor_member_id = p_member;
  DELETE FROM consent_grant WHERE member_id = p_member;
  DELETE FROM location_precision_setting WHERE member_id = p_member;
  WITH d AS (DELETE FROM member_profile_media WHERE member_id = p_member RETURNING storage_ref)
    SELECT count(*), coalesce(array_agg(storage_ref) FILTER (WHERE storage_ref IS NOT NULL), '{}') INTO n, r FROM d;
  IF n > 0 THEN del := del || jsonb_build_object('profile_photos', n); refs := refs || r; END IF;
  DELETE FROM member_interest WHERE member_id = p_member;
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n > 0 THEN del := del || jsonb_build_object('interests', n); END IF;
  DELETE FROM member_gender WHERE member_id = p_member;
  DELETE FROM member_profile WHERE member_id = p_member;
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n > 0 THEN del := del || jsonb_build_object('profile', n); END IF;

  SELECT coalesce(sum(value::int), 0) INTO total FROM jsonb_each_text(del);
  IF total + coalesce((SELECT sum(value::int) FROM jsonb_each_text(pse)), 0) > 0 THEN
    INSERT INTO erasure_receipt (tombstone, deleted, pseudonymised) VALUES (T, del, pse);
    retained := retained || jsonb_build_object('kind', 'deletion_receipt', 'reason', 'One line (one-way deletion id, date, counts) proving the deletion was done.');
  END IF;
  RETURN jsonb_build_object('deleted', del, 'pseudonymised', pse, 'files', to_jsonb(refs), 'retained', retained, 'total', total);
END;
$$;

REVOKE ALL ON FUNCTION milavn_platform.erase_member(uuid, text[]) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION milavn_platform.erase_member(uuid, text[]) TO milavn_app;
