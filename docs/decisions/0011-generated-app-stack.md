# 0011. Generated-app stack

- **Status:** Accepted
- **Date:** 2026-08-07
- **Phase:** 4 (engine · architecture)

## Context
Scio's own stack is locked (ADR-0004..0008), but not the stack Scio *generates apps in*.
Layer B (architecture) and Layer C (build decomposition) cannot be concrete without it.
Competitors lock theirs (Lovable ~ React + Vite + Tailwind + Supabase) because a fixed target
stack is the single biggest reliability multiplier for LLM-generated code.

## Decision
Generated apps use **Next.js + TypeScript + Tailwind + Supabase** (Postgres, auth, storage) —
fixed and opinionated.

## Rationale
- A locked stack makes LLM output far more reliable (same reason competitors lock theirs).
- Next.js + TS + Tailwind is the most LLM-reliable web-app pattern; one framework for front
  and back (simpler decomposition).
- Close to our own stack — we dogfood.
- Supabase gives **secure-by-default** (row-level security) and a fast path to a running app
  with *minimal* LLM-generated security code — hitting both "best result" and our
  developer-grade / security wedge.
- Doesn't break the ownership promise: Supabase is open-source and self-hostable, and the code
  is standard — the user owns it and can take it.

## Consequences
- Fixed = reliable but less flexible.
- Supabase is a dependency in every generated app (mitigated: owned + self-hostable).
- Enables the generation playbook (house rules) and tight per-package context.
- A "plain Postgres, no BaaS" variant may come later for purists.

## Alternatives considered
- Plain Postgres + hand-rolled auth — rejected for MVP; more LLM-generated security code, less reliable.
- A non-fixed / flexible stack — rejected; it kills LLM reliability, which is the whole point.
