# SPIKE — sandbox + marking→code

**This is a spike, not production code.** It exists to prove the hardest mechanic in the
product cheaply and locally before we build it for real (ADR-0005, backlog B039). Nothing
here is wired into `apps/*`, and none of it should be.

**Read [FINDINGS.md](FINDINGS.md) first** — the verdict and the two findings that change how
the real core gets built.

## Run it

```bash
cd spikes/sandbox-marking
python3 -m venv .venv && .venv/bin/pip install playwright pytest
cd example-app && npm install && cd ..

.venv/bin/python run_spike.py                # the full chain, end to end
.venv/bin/python experiment_id_stability.py  # do ids survive a regeneration?
.venv/bin/python -m pytest tests/            # fast tests, no browser needed
```

Screenshots and `results.json` land in `out/`. Both scripts restore `example-app/` to its
committed state when they finish.

## What it does

1. **Starts a sandbox** and serves a live preview of a small Next.js app.
2. **Looks at it** — screenshot plus console, with source URLs (the vision loop's senses).
3. **Resolves a click** at (x, y) to `data-scio-id` → build package → file and line.
4. **Makes a directed change** that edits only that package's files.
5. **Proves the isolation** by hashing every tracked file before and after.

The sandbox runs behind `SandboxProvider`, so the Azure implementation slots in without the
layers above knowing. In this environment there is no Docker daemon, so it ran as a local
process — which proves the mechanic but **not** isolation. See FINDINGS.md.
