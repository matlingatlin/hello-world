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

---

## Prompt injection: the surface, as it actually stands (B104, 2026-08-22)

The gates constrain what a model may **produce** — the instrumentation verifier,
the validation agents and the console classifier are code, and code cannot be
talked out of its opinion. Nothing constrained what a model was **told**. This is
the first pass over that: what enters a prompt from outside, what it could do,
and what stops it.

### Where text we do not control enters a prompt

| Path | Whose words | Reaches | Worst realistic outcome |
|---|---|---|---|
| The wizard conversation | the user's own | extraction → spec → Layer B → Layer C → codegen | Their own app is built wrong. It is their build; the cost is theirs. But the text travels: a spec becomes a contract and a contract becomes code, so it is fenced. |
| **The running app's console and rendered text** | a model's, via code a model wrote | the critique's evidence | **The sharp one.** The defendant addresses the jury: a page that renders "all criteria are met" is asking the judge to agree with it. Outcome would be a dishonest honest status — the one thing this product sells. |
| Design markings | the user's note **plus text scraped from the DOM** | the directed-change prompt | A change request that reads as an instruction to the builder. |
| **Catalog entries** | *another tenant's* build (ADR-0016) | the ambiguity-resolution prompt | The only prompt in the engine carrying text across tenants. Bounded: the reply is matched against the candidate ids, so the worst case is a worse component chosen. |
| The generated app's own files | a model's | every repair prompt | An instruction written into the code in one attempt is quoted back in the next. Self-perpetuating, not escalating. |

### Controls, weakest to strongest

1. **Fencing and labelling** (`execution/untrusted.py`). Every path above wraps
   its third-party text in a marked block, and a payload cannot end its own
   fence — the delimiters are stripped out of it first. The system prompts say
   what a fenced block is: data to read, never instruction to follow, and an
   attempt to direct the model is a finding to report rather than an order.
   This is hygiene. It raises the cost of an attack; it does not make one
   impossible, and it should never be described as if it did.

2. **Structured replies.** Every model answer that matters is parsed into a
   typed shape and validated. A critique that cannot be parsed is a **failure**,
   never a pass. A "pass" carrying an unmet criterion is rewritten to a failure.
   An extraction claiming a field was *stated* is dropped unless it cites a
   message the user actually sent, and it may never overwrite what the user
   corrected by hand.

3. **The deterministic gates** — and this is what actually protects the user.
   Instrumentation, validation and console classification are code. They run
   after whatever any model said, and their verdicts are not opinions a prompt
   can change. A package that "passes" a critique it talked its way through
   still fails an instrumentation check that finds a missing id.

4. **Blast radius.** The generated app runs with an allow-listed environment
   (B091) — no API key, no catalog database — so an instruction that reaches the
   generated code cannot read a secret that is not there.

### Known and open

- The interaction channel and the screenshot path feed the critique too;
  screenshots are not text and are not fenced. Text rendered **inside an image**
  is not covered by anything here.
- Layers B and C receive the spec's field values rather than the raw transcript.
  They are still the user's words, and they are not fenced today.
- No test proves a real model resists a real injection: that needs keys and a
  measured experiment, not an assertion. What is tested is that the fences hold
  and that the structural rules refuse the shapes a successful injection would
  produce.
