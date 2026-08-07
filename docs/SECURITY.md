# Security & threat model

> Status: skeleton. Core decisions in **Phase 2**; implemented and hardened in **Phase 6**.

## Assets to protect
_User data, generated code, secrets, infrastructure, budget._  (Phase 2)

## Threats to address
- Tenant isolation (one user's app/data must never reach another).  (Phase 2/6)
- Sandbox escape from untrusted generated/executed code.  (Phase 2/6)
- Prompt injection into the agent.  (Phase 2/6)
- Abuse / rate limiting / cost-exhaustion attacks.  (Phase 2/6)
- Content safety of generated output.  (Phase 2/6)
- AuthN / authZ.  (Phase 2)

## Controls
_How each threat above is mitigated._  (Phase 2/6)
