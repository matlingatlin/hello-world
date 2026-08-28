-- Fixture B — "0014_notification_read_at" (the negative control).
-- Additive, backward compatible, no rewrite, no long lock, no data loss.
-- A review of this file must report NO blocking findings. Used by eval E2.

ALTER TABLE "notification" ADD COLUMN IF NOT EXISTS "read_at" TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS "notification_workspace_id_read_idx"
  ON "notification" ("workspace_id", "read");
