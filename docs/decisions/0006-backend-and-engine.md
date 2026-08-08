# 0006. Backend + engine: Node/TS backend, Python engine service

- **Status:** Accepted
- **Date:** 2026-08-07
- **Phase:** 0.2

## Context
The frontend is React + TS. The engine is the most AI-heavy part (matrix, multi-pass,
validation agents, multimodal reference RAG). We weighed one language everywhere vs a
split.

## Decision
- App/backend: **Node.js + TypeScript (NestJS)** — API, auth, projects, versions, billing,
  job orchestration, streaming to the client. Shares types with the React frontend.
- Engine: **a separate Python service (FastAPI + Pydantic)** — matrix, multi-pass,
  extraction, validation agents, RAG. Runs the Agent SDK (Python) + provider SDKs.

## Consequences
- Python gives the richest ecosystem exactly where the engine needs it (image handling,
  embeddings, document parsing, RAG). The Agent SDK exists in Python too, so nothing is
  lost on the SDK side.
- Cost: two runtimes to deploy and two dependency trees.
- The seam is neutralised **schema-first**: Pydantic models for the shared objects (spec,
  whole, generation request/result) are the source of truth, and we generate TS types from
  them, so the boundary is typed on both sides.
- Clean typed boundary (HTTP/gRPC) + a job queue between backend and engine (multi-pass is
  long-running; e.g. BullMQ/Redis or an Azure-native queue).
- Fits our service-oriented architecture (the sandbox is already its own service).

## Alternatives considered
- All-TypeScript (backend + engine) — simplest, shared types throughout, but fights the
  current where Python's AI/RAG ecosystem is strongest.
- All-Python — loses type sharing with the React frontend.
