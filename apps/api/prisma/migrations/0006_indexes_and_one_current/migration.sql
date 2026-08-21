-- Indexes on the queries that actually run, and one row that means "current".
--
-- Prisma does not create indexes for foreign keys on PostgreSQL, so the lookup
-- that happens on EVERY request — project.workspace_id, injected by the
-- workspace scope — was a sequential scan. (user.clerk_user_id was already
-- covered: it carries a field-level @unique, which does create an index. The
-- version tables are covered by their (project_id, number) unique constraints.)
CREATE INDEX IF NOT EXISTS "project_workspace_id_idx" ON "project" ("workspace_id");
CREATE INDEX IF NOT EXISTS "project_workspace_id_deleted_at_idx" ON "project" ("workspace_id", "deleted_at");
CREATE INDEX IF NOT EXISTS "user_workspace_id_idx" ON "user" ("workspace_id");
CREATE INDEX IF NOT EXISTS "message_project_id_idx" ON "message" ("project_id");
CREATE INDEX IF NOT EXISTS "usage_event_workspace_id_idx" ON "usage_event" ("workspace_id");
CREATE INDEX IF NOT EXISTS "usage_event_project_id_idx" ON "usage_event" ("project_id");
CREATE INDEX IF NOT EXISTS "notification_workspace_id_user_id_idx" ON "notification" ("workspace_id", "user_id");
CREATE INDEX IF NOT EXISTS "audit_log_workspace_id_idx" ON "audit_log" ("workspace_id");
CREATE INDEX IF NOT EXISTS "deployment_project_id_idx" ON "deployment" ("project_id");
CREATE INDEX IF NOT EXISTS "reference_asset_project_id_idx" ON "reference_asset" ("project_id");
CREATE INDEX IF NOT EXISTS "build_version_spec_version_id_idx" ON "build_version" ("spec_version_id");
CREATE INDEX IF NOT EXISTS "build_version_design_version_id_idx" ON "build_version" ("design_version_id");
CREATE INDEX IF NOT EXISTS "deployment_build_version_id_idx" ON "deployment" ("build_version_id");
CREATE INDEX IF NOT EXISTS "reference_embedding_project_id_idx" ON "reference_embedding" ("project_id");
CREATE INDEX IF NOT EXISTS "reference_embedding_asset_id_idx" ON "reference_embedding" ("asset_id");

-- "Exactly one version is current" was an invariant four separate code paths
-- promised and none of them enforced: each read every row, un-flagged the
-- current one, then created a new one, with no transaction between the two
-- writes. A crash in the middle left a project with NO current version, which
-- every read path reads as "no spec/build/design exists".
--
-- A partial unique index makes the database refuse the second row, so the
-- invariant survives a crash, a race and a fourth caller.
CREATE UNIQUE INDEX IF NOT EXISTS "spec_version_one_current_per_project"
  ON "spec_version" ("project_id") WHERE "is_current";
CREATE UNIQUE INDEX IF NOT EXISTS "build_version_one_current_per_project"
  ON "build_version" ("project_id") WHERE "is_current";
CREATE UNIQUE INDEX IF NOT EXISTS "design_version_one_current_per_project"
  ON "design_version" ("project_id") WHERE "is_current";
