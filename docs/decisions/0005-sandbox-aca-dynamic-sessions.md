# 0005. Sandbox: Azure Container Apps dynamic sessions (custom container)

- **Status:** Accepted (with a spike; feature is in preview)
- **Date:** 2026-08-07
- **Phase:** 0.2

## Context
User-generated apps must run in isolated, secure environments. This is the hardest
technical piece and a major cost driver. Azure (ADR-0004) offers a purpose-built option.

## Decision
Use Azure Container Apps dynamic sessions, custom container type, as the per-project
sandbox for MVP. Wrap it behind a swappable sandbox interface in our code.

## Consequences
- Designed to run untrusted / AI-generated code in isolated sandboxes; each session runs
  in its own Hyper-V sandbox (hypervisor-level isolation) with optional network isolation.
- Prewarmed session pools give millisecond startup; scales to many concurrent sessions;
  pay-per-use with a free tier.
- Custom container lets us run our own Node/Vite toolchain and a dev server the user
  browses; the managed code-interpreter type can serve the vision-loop's execution.
- Cost control is essential: idle timeouts (cooldown), caps on concurrent sessions,
  aggressive pause/stop.

## Risks / follow-ups
- Dynamic sessions is in preview — verify GA status before hard production commitment.
- Spike early: hosting a browsable dev server AND rendering for the vision loop is the
  pattern to prove before full commitment. The swappable interface lets us move to E2B or
  Modal if needed.

## Alternatives considered
- E2B / Modal — purpose-built for AI code, great DX, but off-Azure vendors (separate bill,
  data leaves the cloud boundary).
- Daytona — newer, less mature for this.
- Self-managed Firecracker — max control/efficiency at scale, but we would build and
  operate the isolation layer ourselves. Wrong place to spend time now.
