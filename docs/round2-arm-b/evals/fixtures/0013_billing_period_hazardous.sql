-- Fixture A — "0013_billing_period" (hazardous).
-- Written against the real Scio schema (apps/api/prisma/migrations, docs/DATA-MODEL.md).
-- Used by evals E1, E3, E5, E6. Every hazard here is deliberate; the expected
-- finding table lives in docs/round2-arm-b/evals/migration-reviewer-evals.md.

-- Metering rows get the period they belong to.
ALTER TABLE "usage_event" ADD COLUMN "billing_period" TEXT NOT NULL DEFAULT '2026-08';
UPDATE "usage_event" SET "billing_period" = to_char("created_at", 'YYYY-MM');

-- Cost has been written on every row for months; make it a promise.
ALTER TABLE "usage_event" ALTER COLUMN "cost" SET NOT NULL;

-- The billing screen groups by workspace and period.
CREATE INDEX "usage_event_workspace_id_billing_period_idx"
  ON "usage_event" ("workspace_id", "billing_period");

-- Soft delete never shipped; drop the column.
ALTER TABLE "project" DROP COLUMN "deleted_at";

-- "spend" is what the estimate screen calls it.
ALTER TABLE "build_job" RENAME COLUMN "cost_usd" TO "spend_usd";

-- Notifications should die with their user.
ALTER TABLE "notification"
  ADD CONSTRAINT "notification_user_id_fkey"
  FOREIGN KEY ("user_id") REFERENCES "user"("id") ON DELETE CASCADE;
