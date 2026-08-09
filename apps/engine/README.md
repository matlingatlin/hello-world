# scio-engine — the AI engine service

Python + FastAPI + Pydantic (ADR-0006). Two things live here today:

- **Layer A** — the intake schema from `docs/INTAKE-SCHEMA.md` as typed models,
  the `is_buildable()` gate, trigger detection, downstream-tag mapping.
- **Execution machinery** — the provider abstraction, the capability matrix, and
  the multi-pass relay: the layer everything else (Layer B's judgment, extraction,
  codegen) runs on top of.

Requirements extraction (4.3), Layer B's architecture logic (B034), and codegen
are still to come.

## Run locally

```bash
cd apps/engine
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
uvicorn scio_engine.main:app --reload --port 8000   # http://localhost:8000/docs
```

Try the gate:

```bash
curl -s -X POST localhost:8000/intake/validate -H "Content-Type: application/json" -d '{
  "purpose": {"value": "Guests book a table."},
  "users_and_roles": {"value": ["guests", "staff"]}
}'
# -> buildable: false, missing core fields, and role_permissions triggered by the two roles
```

## Test & lint

```bash
pytest        # gate + API tests
ruff check .  # lint
```

## Run the multi-pass relay

`POST /generate` picks the best models for the task from the capability matrix,
runs the relay, and streams each pass as SSE (`narration` → one `pass` per pass →
`result`):

```bash
curl -N -X POST localhost:8000/generate -H "Content-Type: application/json" -d '{
  "task": "codegen",
  "prompt": "Build a booking form",
  "options": {"passes": 4}
}'
```

`POST /generate/plan` returns the same selection and narration without spending
anything, and `GET /matrix/tasks` lists the task types with their ranked models.

**Without API keys** the engine binds every vendor to the deterministic
`FakeProvider` — the whole flow runs, output is reproducible, nothing is spent.
`GET /health` reports which mode you're in (`"providers": "fake" | "real"`).

**With real models**, install the SDKs and set the keys:

```bash
pip install -e ".[dev,providers]"
export ANTHROPIC_API_KEY=...   # and/or OPENAI_API_KEY / GOOGLE_API_KEY
# AZURE_OPENAI_ENDPOINT routes OpenAI calls through Azure (ADR-0004)
```

Any key present switches to real providers; `SCIO_FAKE_PROVIDERS=1` forces fakes back on.

## Layout

- `src/scio_engine/intake/schema.py` — FieldMeta (value/source/confidence/provenance),
  DownstreamTag, AppSpec (core / conditional / defaulted-and-flagged fields), FIELD_TAGS.
- `src/scio_engine/intake/gate.py` — `is_buildable()`, `triggered_conditionals()`,
  `downstream_tags()`, `assumed_fields()`.
- `src/scio_engine/execution/provider.py` — `ModelProvider` interface, Anthropic /
  OpenAI / Google implementations, `FakeProvider`, and the registry that binds them.
- `src/scio_engine/execution/matrix.yaml` — the capability matrix: task types →
  ranked models with cost/latency/context metadata. **Edit this file** to change
  rankings; no code change needed.
- `src/scio_engine/execution/matrix.py` — loading, validation, `top_n(task, n)`.
- `src/scio_engine/execution/narration.py` — the user-facing "here's what I'll run".
- `src/scio_engine/execution/relay.py` — the multi-pass relay, pass planning,
  structured hand-off, pass cap, timeouts/retries, budget hook.
- `src/scio_engine/main.py` — FastAPI app: `/health`, `/intake/validate`,
  `/matrix/tasks`, `/generate/plan`, `/generate`.
