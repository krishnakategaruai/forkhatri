-- [IMP-B — critique W2 (women's safety), 2026-09-29] Pre-accept calling had
-- one setting, and the copy on it promised "your number is never shown
-- outside your hours". That was not true: a tel: link hands the number over
-- for good, and a wa.me link does the same. The switch stays; the poster now
-- also chooses HOW people may reach them before accepting:
--   whatsapp_only      people can message on WhatsApp, never ring the phone
--                      (the default for new posts: a message can wait, a
--                      2 a.m. call cannot);
--   call_and_whatsapp  both, as before.
-- Either way the caller sees the number; the copy now says so. The real fix
-- is a masked/proxy number (Exotel/Knowlarity class), logged as a vendor
-- item in 09a-external-dependencies.md.
-- Existing posts that already allow pre-accept calling keep calls on (they
-- chose "calls"); every other row, and every new post, gets whatsapp_only.
-- Traces to: FR02, FR24, critique W2, VISION-2040 item 9 (women-safe mode)
ALTER TABLE vyapar_opportunities.opportunities
  ADD COLUMN IF NOT EXISTS precall_channel text NOT NULL DEFAULT 'whatsapp_only';
ALTER TABLE vyapar_opportunities.opportunities DROP CONSTRAINT IF EXISTS opportunities_precall_channel_check;
ALTER TABLE vyapar_opportunities.opportunities ADD CONSTRAINT opportunities_precall_channel_check
  CHECK (precall_channel IN ('call_and_whatsapp','whatsapp_only'));
DO $$
BEGIN
  -- one-time backfill, only while no row has been set to calls yet (keeps re-runs idempotent)
  IF NOT EXISTS (SELECT 1 FROM vyapar_opportunities.opportunities WHERE precall_channel = 'call_and_whatsapp') THEN
    UPDATE vyapar_opportunities.opportunities SET precall_channel = 'call_and_whatsapp' WHERE allow_precall;
  END IF;
END $$;
COMMENT ON COLUMN vyapar_opportunities.opportunities.precall_channel IS
  '[IMP-B/W2] How people may reach the poster before acceptance: whatsapp_only (default) or call_and_whatsapp. The number is visible to whoever uses either.';
