-- What a build actually cost, on the build's own record.
--
-- usage_event is the per-workspace metering ledger and keeps being written; a
-- build_version is the record of ONE build and should be readable on its own.
-- Nullable on purpose: builds recorded before this have no figure, and writing
-- 0 would be a claim rather than an absence.
ALTER TABLE "build_version" ADD COLUMN "cost_usd" DECIMAL(65,30);
ALTER TABLE "build_version" ADD COLUMN "tokens" INTEGER;

-- Which spec the cached whole + estimate describe.
--
-- Invalidation is by construction today: every path that writes draft_spec
-- writes them together. This is what keeps that true the day a fourth writer
-- appears — a mismatch means recompute, instead of showing a confident summary
-- of a spec that no longer exists.
ALTER TABLE "project" ADD COLUMN "draft_confirmation_hash" TEXT;
