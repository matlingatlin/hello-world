-- A retry must not be a second bill.
--
-- POST /build had no idempotency key, so anything that made a client send the
-- request twice — a reload, a dropped stream, an impatient second click after
-- the first one appeared to do nothing — started a second build and charged for
-- it. The in-flight case was already refused (a build lock), but the case where
-- the first build had *finished* and the client never heard was not: it built
-- the whole app again.
--
-- The key is scoped to the project, and the index is partial so the builds that
-- predate this (and any build made without a key) do not all collide on NULL.
ALTER TABLE "build_version" ADD COLUMN IF NOT EXISTS "idempotency_key" TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS "build_version_project_id_idempotency_key_key"
  ON "build_version" ("project_id", "idempotency_key")
  WHERE "idempotency_key" IS NOT NULL;
