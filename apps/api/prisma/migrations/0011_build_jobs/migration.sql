-- A build is a job, not a request that happens to take forty minutes (B094).
--
-- Until now a build existed only as a stack frame in one api process and one
-- engine process. Restart either and a forty-minute build that had spent real
-- money was gone with no record of how far it got, leaving the project saying
-- "building" until a 90-minute lock aged out. Nobody could cancel one either:
-- the only stop was a spend ceiling nobody chose in the moment.
--
-- This is ADR-0020's first slice: the row. The queue and the worker are still
-- proposed — what the row buys on its own is a build you can find after a
-- restart, and one you can stop.
CREATE TABLE IF NOT EXISTS "build_job" (
  "id"              UUID PRIMARY KEY,
  "project_id"      UUID NOT NULL REFERENCES "project"("id"),
  "spec_version_id" UUID NOT NULL REFERENCES "spec_version"("id"),
  "workspace_id"    UUID NOT NULL REFERENCES "workspace"("id"),
  -- queued | running | succeeded | failed | cancelled
  "status"          TEXT NOT NULL DEFAULT 'queued',
  "idempotency_key" TEXT,
  -- What the build last said. A reconnecting client can be told where it got to
  -- instead of only whether it ended.
  "last_event"      TEXT NOT NULL DEFAULT '',
  "parts_done"      INTEGER NOT NULL DEFAULT 0,
  "parts_total"     INTEGER NOT NULL DEFAULT 0,
  "failure"         TEXT NOT NULL DEFAULT '',
  -- Bumped as events arrive. A job whose heartbeat has gone quiet is a job
  -- whose process died, and it is reaped rather than left "running" forever.
  "heartbeat_at"    TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "created_at"      TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "finished_at"     TIMESTAMP(3)
);

CREATE INDEX IF NOT EXISTS "build_job_project_id_status_idx"
  ON "build_job" ("project_id", "status");
CREATE INDEX IF NOT EXISTS "build_job_workspace_id_idx" ON "build_job" ("workspace_id");

-- One build at a time per project, enforced by the database rather than by a
-- read-then-write in the api: two builds share one workspace, and the second
-- deletes the first one's files.
CREATE UNIQUE INDEX IF NOT EXISTS "build_job_one_live_per_project"
  ON "build_job" ("project_id")
  WHERE "status" IN ('queued', 'running');
