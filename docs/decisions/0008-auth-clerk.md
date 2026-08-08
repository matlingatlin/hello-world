# 0008. Auth: Clerk (MVP)

- **Status:** Accepted (deliberate exception to the Azure-native default; swappable)
- **Date:** 2026-08-07
- **Phase:** 0.2

## Context
We need authentication. Auth is undifferentiated, security-critical heavy lifting; a
specialist provider is safer than hand-rolling. Our kil includes small teams (needs orgs).

## Decision
Use **Clerk** for MVP, behind our own session/user interface so it stays swappable. This is
a deliberate exception to our Azure-native default.

## Consequences
- Excellent DX (drop-in React components, sessions, MFA, social login) and built-in
  organisations/teams — speed for a small team.
- Exception rationale: identities are exactly what an auth provider is built to protect, so
  the cloud-boundary argument (applied to generated code + RAG) weighs less here.
- Backend verifies Clerk JWTs; the Python engine can validate the same tokens.

## Reconsider / alternatives
- **Microsoft Entra External ID** — the Azure-native alternative (identities in your cloud
  boundary), clunkier DX. The natural switch if hard residency/enterprise requirements
  appear (our kil can grow there bottom-up).
- Auth0 — mature but costlier.
- Supabase Auth — pulls in a Supabase dependency we otherwise don't have.
- Hand-rolled — rejected; never hand-roll auth.
