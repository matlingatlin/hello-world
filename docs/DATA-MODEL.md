# Scio — Data model

Postgres (Azure Flexible Server, ADR-0007) with pgvector. Every table below carries uuid
`id` PKs and `created_at`; mutable tables also carry `updated_at`. All app data is scoped
to a `workspace` for tenant isolation. Version *code* lives in git; the DB holds metadata.
See ADR-0009 for rationale.

## Entities

### workspace  (the tenant boundary)
- name · plan (starter | builder | team)
- MVP: one workspace per user, auto-created on signup.

### user
- clerk_user_id (unique) · email · workspace_id (fk) · role (owner | member)
- Links a Clerk identity to a workspace.

### project
- workspace_id (fk) · name · type (app | website | automation; MVP: app)
- status (draft | building | ready | error) · deleted_at (nullable, soft delete)

### message  (wizard conversation / context)
- project_id (fk) · role (user | scio) · content (text)

### spec_version  (frozen spec/whole contract)
- project_id (fk) · number (int) · content (jsonb) · assumptions (jsonb) · is_current (bool)
- unique(project_id, number)

### design_version  (approved design contract — Level 2)
- project_id (fk) · number · ref (storage pointer/snapshot) · is_current
- unique(project_id, number)

### build_version  (the version timeline)
- project_id (fk) · number · description (plain-language) · git_sha
- honest_status (jsonb: { passed, needs_look[] })
- spec_version_id (fk) · design_version_id (fk, nullable) · is_current
- unique(project_id, number). Restore = insert a new row; never delete.

### deployment  (publish targets)
- project_id (fk) · build_version_id (fk) · target (scio_url | own_infra)
- url · status (pending | live | failed)

### reference_asset  (tagged RAG uploads)
- project_id (fk) · kind (color | font | layout | document | brand | other)
- filename · storage_url · extracted (jsonb)

### reference_embedding  (pgvector, retrieval)
- project_id (fk) · asset_id (fk) · chunk (text) · embedding (vector)
- vector index (hnsw/ivfflat)

### usage_event  (metering for cost/billing)
- workspace_id (fk) · project_id (fk, nullable) · kind (generation | critique | sandbox | …)
- model (text) · amount (numeric) · cost (numeric)

### notification
- workspace_id (fk) · user_id (fk) · kind (build_done | needs_look | limit | cost | update)
- title · body · read (bool)

### audit_log  (security)
- workspace_id (fk) · actor · action · target · metadata (jsonb)

## Notes
- Secrets are never stored here — Azure secrets manager only.
- Object storage holds uploaded files; the DB holds pointers (storage_url).
- Billing/subscription tables: deferred to Phase 12.
