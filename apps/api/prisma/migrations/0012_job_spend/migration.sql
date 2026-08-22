-- What a build spent, on the build's own row — including the builds that never
-- finished.
--
-- The ledger was written in `persist()`, and `persist()` runs only when a
-- `finished` event arrives. So a build that was cancelled, crashed, or errored
-- recorded ZERO spend, while the engine had really spent the money and said so
-- in every `package` event along the way. ADR-0020 states the opposite as an
-- invariant — "a cancellation that quietly forgave the cost would be a hole, and
-- an exploitable one" — and it was: cancel a second before the end and the
-- ledger stayed at zero.
--
-- Kept on the job rather than only in `usage_event` because the job is the thing
-- that exists while the spending happens: it is where the running total belongs,
-- and it is what the ledger row is written from on any exit.
ALTER TABLE "build_job" ADD COLUMN IF NOT EXISTS "cost_usd" DECIMAL(10,4) NOT NULL DEFAULT 0;
ALTER TABLE "build_job" ADD COLUMN IF NOT EXISTS "tokens" INTEGER NOT NULL DEFAULT 0;
