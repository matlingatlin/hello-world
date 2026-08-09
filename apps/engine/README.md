# scio-engine — the AI engine service

Python + FastAPI + Pydantic (ADR-0006). Currently: **Layer A** — the intake schema
from `docs/INTAKE-SCHEMA.md` as typed models, the `is_buildable()` gate, trigger
detection, and downstream-tag mapping. No extraction and no LLM calls yet — the
matrix + multi-pass relay and extraction (4.3) land in later kickoffs (B031).

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

## Layout

- `src/scio_engine/intake/schema.py` — FieldMeta (value/source/confidence/provenance),
  DownstreamTag, AppSpec (core / conditional / defaulted-and-flagged fields), FIELD_TAGS.
- `src/scio_engine/intake/gate.py` — `is_buildable()`, `triggered_conditionals()`,
  `downstream_tags()`, `assumed_fields()`.
- `src/scio_engine/main.py` — FastAPI app: `GET /health`, `POST /intake/validate`.
