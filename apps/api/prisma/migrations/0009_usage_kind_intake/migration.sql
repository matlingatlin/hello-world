-- The wizard spends money too.
--
-- One relay call per user message, and until now the only spend in the product
-- the ledger could not see at all — not folded into another kind, simply absent.
ALTER TYPE "UsageKind" ADD VALUE IF NOT EXISTS 'intake';
