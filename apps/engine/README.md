# scio-engine — the AI engine service

Python + FastAPI + Pydantic (ADR-0006). Two things live here today:

- **Layer A** — the intake schema from `docs/INTAKE-SCHEMA.md` as typed models,
  the `is_buildable()` gate, trigger detection, downstream-tag mapping.
- **Execution machinery** — the provider abstraction, the capability matrix, and
  the multi-pass relay: the layer everything else runs on top of.
- **Layer B** — a buildable spec becomes the whole, a machine-readable
  architecture graph, and the generation playbook, validated before generation
  (`docs/LAYER-B.md`).
- **Layer C** — the architecture becomes a validated, dependency-ordered plan of
  small contract-bearing build packages (`docs/LAYER-C.md`).

That completes the A -> B -> C brain. Requirements extraction (4.3), the builder,
the sandbox and the marking->code core are still to come.

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

## Run Layer B

`POST /architecture` takes a **buildable** spec (Layer A's gate must have opened)
and returns the whole, the architecture graph, the playbook and the validation:

```bash
curl -s -X POST localhost:8000/architecture -H "Content-Type: application/json" -d '{
  "spec": {
    "purpose": {"value": "Guests book a table and get a confirmation."},
    "users_and_roles": {"value": ["guests", "staff"]},
    "entities": {"value": ["bookings", "tables", "guests"]},
    "key_actions": {"value": ["book a table", "cancel a booking", "see todays bookings"]},
    "sign_in": {"value": "email link"},
    "role_permissions": {"value": "staff see all bookings; guests only their own"},
    "data_ownership_sensitivity": {"value": {"owner": "you", "sensitive": false}},
    "non_goals": {"value": ["no payments for now"]}
  }
}'
```

Everything except the whole is derived deterministically, so the same spec always
yields the same architecture. The whole runs through the relay — with no API keys
that is the FakeProvider, and if no model answers at all it falls back to a plain
narrative built from the spec rather than leaving the spec gate empty.

A spec that hasn't passed the gate gets a 422 listing what's missing; an
architecture that fails validation still returns, with `validation.valid: false`
and `revisit_fields` naming the spec fields the wizard should reopen.

## Run Layer C

`POST /plan` takes a Layer B architecture and returns the build plan: ordered
packages, the dependency graph, the validation result, and each package's
assembled contract prompt.

```bash
# take the architecture straight from /architecture:
curl -s -X POST localhost:8000/architecture -H "Content-Type: application/json" \
  -d @spec.json > arch.json
python3 -c "import json; d=json.load(open('arch.json')); \
  json.dump({'architecture': d['architecture'], 'whole': d['whole']['narrative']}, \
  open('plan-req.json','w'))"
curl -s -X POST localhost:8000/plan -H "Content-Type: application/json" -d @plan-req.json
```

Decomposition and ordering are deterministic. The relay is consulted only when
the rules leave something genuinely ambiguous (an operation the architecture
couldn't attach to an entity); pass `"use_judgment": false` to skip even that.

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
- `src/scio_engine/layerb/vocabulary.py` — canonical vocabulary: one name per
  concept, used across the architecture, the prompts and the generated code.
- `src/scio_engine/layerb/architecture.py` — the typed, sliceable graph.
- `src/scio_engine/layerb/derive.py` — the deterministic backbone (no LLM):
  entities → tables, sign_in → auth, roles → RBAC, actions → operations + screens,
  sensitivity → security posture, conditionals → connectors, look → tokens.
- `src/scio_engine/layerb/validate.py` — the rule checks that run before generation.
- `src/scio_engine/layerb/playbook.yaml` — the house rules. **Edit this file** to
  change how every app is built; `playbook.py` assembles them into build context.
- `src/scio_engine/layerb/whole.py` — the narrative, generated via the relay from
  a grounded fact set.
- `src/scio_engine/layerb/service.py` — derive → validate → generate, in that order.
- `src/scio_engine/layerc/plan.py` — BuildPackage / BuildPlan / NodeRef.
- `src/scio_engine/layerc/decompose.py` — the deterministic planner: foundation,
  schema, auth, one package per feature, connectors, tokens; topological ordering.
- `src/scio_engine/layerc/contract.py` — assembles each package's prompt: its
  slice in full detail, its dependencies' *interfaces* only, the why, the rules.
- `src/scio_engine/layerc/validate.py` — coverage, acyclicity, contract checks.
- `src/scio_engine/layerc/judgment.py` — the one place the relay is consulted.
- `src/scio_engine/main.py` — FastAPI app: `/health`, `/intake/validate`,
  `/matrix/tasks`, `/generate/plan`, `/generate`, `/architecture`, `/plan`.
