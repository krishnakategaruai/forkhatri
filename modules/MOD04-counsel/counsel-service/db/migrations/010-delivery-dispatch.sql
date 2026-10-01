-- The delivery queue is now sent by the shared ForKhatri dispatcher
-- (shared/forkhatri-integrations delivery.Dispatcher): retries need a due time
-- and the provider's message id.
SET search_path TO counsel, public;

ALTER TABLE delivery ADD COLUMN IF NOT EXISTS next_attempt_at timestamptz NOT NULL DEFAULT now();
ALTER TABLE delivery ADD COLUMN IF NOT EXISTS provider text;
ALTER TABLE delivery ADD COLUMN IF NOT EXISTS provider_ref text;
CREATE INDEX IF NOT EXISTS delivery_due_idx ON delivery (next_attempt_at) WHERE status IN ('queued', 'retry');
