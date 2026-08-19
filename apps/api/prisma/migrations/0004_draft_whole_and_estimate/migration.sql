-- The confirmation prose and the cost estimate for the working spec.
--
-- They are DERIVED from draft_spec, and deriving them costs a real Layer B +
-- Layer C model call: the first full real run measured GET /projects/:id/intake
-- at 10.6s and 12.7s, because it recomputed both on every request. Loading the
-- wizard or the review screen spent money.
--
-- Stored beside the spec they belong to, and written by every path that writes
-- draft_spec, so they cannot drift from it.
ALTER TABLE "project" ADD COLUMN "draft_whole" TEXT;
ALTER TABLE "project" ADD COLUMN "draft_estimate" JSONB;
