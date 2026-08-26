# apps/engine — Python + FastAPI

The brain. Every model call, every gate, every sandbox lives here; the api owns
none of it.

## The layers

- **Layer A — `intake/`.** Conversation → a typed spec. Extraction, clause
  routing, corrections. A correction is authoritative: it is marked
  `corrected-on-review` and extraction must not overwrite it, or the next turn
  quietly re-files the same mistake.
- **Layer B — `layerb/`.** Spec → architecture, entities, vocabulary.
- **Layer C — `layerc/`.** Architecture → build packages, the unit a build
  actually generates and judges.
- **`builder/`, `execution/`, `library/`, `design/`, `core/`.** The loop, the
  model relay, the component library, directed change, the sandbox.

## Gates decide, prose does not

A package passes because a gate says so. Instrumentation verifier, validation
agents, console classifier, critique, an app-wide typecheck, and B060a/b — does
it work end to end with real data, and can one guest read another's row.
`unjudged` is a real verdict and must never be reported as a pass.

Assembled library parts are judged by `ASSEMBLY_GATES`, not the full `GATES`:
scoring a library component against rules it was never written to produced
"5 of 5" in preview and "4 of 5" in delivery for identical files.

## Spend

`Spend` is **build-scoped, never per relay call**. A "$3.76 ceiling" applied per
invocation authorises $50–80 per build; that bug is fixed and the comment
explaining it carries a rule, not history. `_cost` prices **both** halves of the
bill — a repair attempt re-sends every file it is fixing, so input is a third to
a half of the real invoice.

## Providers, and not spending money by accident

No key configured means `FakeProvider` and `standin` builders — free, and the
default in a fresh clone. **`config.py` reads `apps/engine/.env` at import**, so
a machine with a key there comes up in *real* mode even when the environment
variable is unset. `SCIO_SKIP_ENV_FILE=1` or `SCIO_FAKE_PROVIDERS=1` forces the
free path. Check `curl localhost:8000/health` before clicking anything that
builds: `"providers": "fake"` is free, `"real"` is your card.

The engine refuses to start under `SCIO_ENV=production` with no
`SCIO_ENGINE_TOKEN` — it authenticates nobody without it and spends money on
request.

## Sandbox

`LocalProcessSandbox` refuses to run in production; `LocalDockerSandbox` runs
with memory, CPU, PID and no-new-privileges limits, and **writes our own
Dockerfile, always** — the generated app is exactly the thing whose Dockerfile
must not be trusted. `AcaSandbox` is not implemented (B122); there is no
isolating sandbox for production yet, and no network policy on containers (B118).

## Tests

`apps/engine/.venv/bin/python -m pytest -q`, ~3.5 minutes, 655 passing / 6
skipped. Dependencies are pinned in `requirements.lock` — `pyproject.toml`'s
ranges are not the source of truth for what CI installs.
