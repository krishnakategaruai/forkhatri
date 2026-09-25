-- =============================================================================
-- 039 — The Hinge-style content is for connected candidates, unless its owner
--       publishes it (product owner, 2026-09-21).
--
-- WHY:
--   Migration 027 opened a searchable candidate's whole attribute set to any
--   signed-in member, which was right for BIODATA — a parent evaluating a
--   match needs marital status, family, diet, horoscope before anyone is asked
--   to connect. It is wrong for the two categories added since:
--
--     * `in_my_words` — the prompt answers. These are written by a candidate
--       for another candidate: "On living with family after marriage, I
--       picture...". Before 039 every signed-in member could read them,
--       including the parents of people the writer has never met.
--     * `outlook` — the ten-question activity's answers, for the same reason.
--
--   The product owner's rule: she requests, he accepts, and then she can read
--   them — with the owner free to publish individual items so that anyone,
--   parents included, may see those.
--
--   This matches the baseline's own selective-sharing principle (§16):
--   "Acceptance opens the door; it does not open everything inside the house."
--   It is NOT the teaser-profile pattern §8.1 forbids: the biodata a family
--   needs to judge a match stays fully readable before acceptance. What moves
--   behind the door is only the candidate-to-candidate voice.
--
--   Publishing is per item, carried on the value itself (`"public": true`)
--   rather than a separate table: the visibility of a sentence belongs with
--   the sentence, and `profile_attribute.value` is already free-form JSON
--   whose shape the editor owns.
--
--   The connected view does not come through this function at all — it reads
--   `profile_attribute` under `candidate_info`, which only the two parties to
--   an accepted connection hold — so nothing here narrows what a connected
--   candidate sees.
-- Idempotent: safe to re-run.
-- =============================================================================

CREATE OR REPLACE FUNCTION mangaly_profile.public_biodata(p_account_id uuid)
RETURNS TABLE (
    category text,
    attribute_key text,
    value jsonb
)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = mangaly_profile, mangaly_discovery, pg_temp
AS $$
    SELECT a.category::text, a.attribute_key, a.value
      FROM mangaly_profile.profile_attribute a
      JOIN mangaly_profile.profile p ON p.id = a.profile_id
     WHERE p.account_id = p_account_id
       AND a.state = 'value'
       AND NULLIF(current_setting('mangaly.account_id', true), '') IS NOT NULL
       AND EXISTS (
           SELECT 1 FROM mangaly_discovery.discovery_profile_index i
            WHERE i.profile_id = p_account_id AND i.searchable
       )
       -- Candidate-to-candidate voice is withheld unless published by its
       -- owner. Every other category behaves exactly as migration 027 set it.
       AND (
             a.category NOT IN ('in_my_words', 'outlook')
          OR COALESCE(a.value ->> 'public', 'false') = 'true'
       );
$$;

REVOKE ALL ON FUNCTION mangaly_profile.public_biodata(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mangaly_profile.public_biodata(uuid) TO mangaly_app;
