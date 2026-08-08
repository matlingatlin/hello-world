# 0007. Database: PostgreSQL (Azure Flexible Server)

- **Status:** Accepted
- **Date:** 2026-08-07
- **Phase:** 0.2

## Context
Data is genuinely relational (users <-> projects <-> versions <-> usage <-> audit) but
also has semi-structured objects (the spec and wholeness anchor), plus embeddings for the
reference RAG.

## Decision
PostgreSQL, managed as Azure Database for PostgreSQL - Flexible Server. JSONB for the
spec/whole objects. pgvector for reference-RAG embeddings, in the same database.

## Consequences
- Relations with integrity + JSONB flexibility in one store; no separate NoSQL needed.
- pgvector keeps embeddings next to the rest — one data store for MVP; a dedicated vector
  DB (Qdrant / Pinecone / Azure AI Search) is an escape hatch behind an interface if scale
  demands it.
- Typed access via an ORM on the TS backend (Prisma, or Drizzle to stay close to SQL);
  backend owns schema + migrations; the Python engine uses the vector tables for RAG.
- Version *content* lives in git (see UX-FLOW/PROJECT-PLAN); the DB holds only
  metadata/pointers, so it stays light. (Where git repos are stored is an open architecture
  point.)
- JSONB must follow the Pydantic/TS types, not become a dumping ground. Confirm pgvector
  version/limits on Flexible Server when building.

## Alternatives considered
- Supabase / Neon — great Postgres DX, but off-Azure (data leaves the boundary).
- Cosmos DB — Azure-native and flexible, but our data is relational; Postgres + JSONB gives
  the flexibility without losing relations.
- Dedicated vector DB from day one — premature; pgvector suffices for MVP.
