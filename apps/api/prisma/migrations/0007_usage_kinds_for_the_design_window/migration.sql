-- Two kinds the ledger could not express.
--
-- usage_event was written by exactly one caller, the delivery build, and typed
-- `generation`. A preview build and a directed change make the same model calls
-- and cost the same real money, and the design window is where the product
-- expects people to spend most of their time — so folding them into
-- `generation` would record the spend and lose the one distinction that makes
-- it useful for pricing.
--
-- PostgreSQL 12+ allows ADD VALUE inside a transaction as long as the value is
-- not used in the same one; Prisma's migration is a transaction and this file
-- only declares.
ALTER TYPE "UsageKind" ADD VALUE IF NOT EXISTS 'preview';
ALTER TYPE "UsageKind" ADD VALUE IF NOT EXISTS 'design_change';
