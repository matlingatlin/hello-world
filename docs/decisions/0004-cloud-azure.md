# 0004. Cloud: Azure

- **Status:** Accepted
- **Date:** 2026-08-07
- **Phase:** 0.2

## Context
We need a cloud. The cost and complexity centres are the engine (multi-pass across
models) and the per-user sandboxes that run untrusted generated code. We want strong
isolation, data residency, a purpose-built sandbox option, and startup credits.

## Decision
Azure.

## Consequences
- OpenAI is available natively via Azure OpenAI Service; Claude and Gemini are called via
  their own provider APIs. The matrix is multi-provider, so model cost is not all on one
  cloud bill (relevant for cost tracking).
- Strong sandbox fit: Azure Container Apps dynamic sessions (see ADR-0005).
- Apply for Microsoft for Startups (Founders Hub) for Azure credits to offset the engine +
  sandbox cost (verify current terms).

## Alternatives considered
- AWS — also strong; chose Azure for the native untrusted-code sandbox (ACA dynamic
  sessions), Azure OpenAI, and Microsoft for Startups credits.
