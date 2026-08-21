-- Every billing question is "spend in a period", and nothing indexed the period.
--
-- 0006 gave usage_event its workspace and project indexes, which serve "whose
-- spend" and leave "since when" to a scan. An invoice is workspace + month.
CREATE INDEX IF NOT EXISTS "usage_event_workspace_id_created_at_idx"
  ON "usage_event" ("workspace_id", "created_at");
