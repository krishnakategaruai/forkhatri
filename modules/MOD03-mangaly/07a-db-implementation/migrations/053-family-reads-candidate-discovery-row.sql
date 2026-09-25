-- =============================================================================
-- 053 — A Home Circle member can read their candidate's own Discovery row.
--
-- WHY (2026-09-24, functional sweep): Discovery reads the seeker's side — who
-- the candidate is looking for, their gender, their ranking snapshot — from the
-- candidate's own `discovery_profile_index` row. Its RLS policy (migration 001)
-- was `searchable = true OR is_self(profile_id)`. So while a candidate is not
-- (yet) searchable — a profile still filling in its discoverability tier, or
-- one the candidate has hidden — every family member searching FOR them read
-- nothing: Discover answered 409 "tell us whether you are looking for a bride
-- or a groom" although the candidate had answered, and a parent's request on
-- the candidate's behalf was refused as "not who you are looking for". Seen
-- with Aditi Kapoor (claimed, active, looking for a groom, not searchable).
--
-- This adds exactly the reader the rest of the circle design already trusts:
-- an account holding an active `family_info` grant on that candidate (the
-- grant a Home Circle membership carries; grants target the candidate's
-- account id, which is this table's key). It exposes nothing to anyone else,
-- and it does not make a non-searchable candidate appear in anyone's results:
-- `search()` filters `searchable` explicitly in its own WHERE clause.
--
-- Idempotent: safe to re-run.
-- =============================================================================

DROP POLICY IF EXISTS discovery_index_searchable_or_owner ON mangaly_discovery.discovery_profile_index;
CREATE POLICY discovery_index_searchable_or_owner ON mangaly_discovery.discovery_profile_index
  USING (
    searchable = true
    OR mangaly_authz.is_self(profile_id)
    OR mangaly_authz.has_scope(profile_id, 'family_info')
  );
