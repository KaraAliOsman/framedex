---
name: testing-framedex
description: Local dev-stack recipe for DEKOPEN E2E testing — Supabase CLI stack, Django/Vite env vars, ESTIMATOR fixture creation, magic-link login via Mailpit, catalog seeding for bow/assembly features.
---

# DEKOPEN local E2E stack

## Start services

1. Supabase local stack: `cd <repo> && /home/ubuntu/.local/bin/supabase start` (CLI 2.116.x in ~/.local/bin; if missing, download the linux-amd64 tarball from supabase/cli releases). Ports: API `:25321`, Postgres `:25322`, Mailpit UI `:25324`. `supabase status -o env` prints `ANON_KEY`/`SERVICE_ROLE_KEY`/`API_URL`.
2. Django: `cd backend && DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:25322/postgres SUPABASE_URL=http://127.0.0.1:25321 SUPABASE_ANON_KEY=<anon> SUPABASE_SERVICE_ROLE_KEY=<svc> SUPABASE_JWT_VERIFY_MODE=auth_server CORS_ALLOWED_ORIGINS=http://127.0.0.1:5173 ../.venv/bin/python manage.py runserver 127.0.0.1:8000 --noreload`. Venv at repo root (`uv venv .venv && uv pip install --python .venv`); `--noreload` means restart after every backend commit.
3. Vite: `export PATH="/home/ubuntu/node22/bin:$PATH"; cd frontend && VITE_SUPABASE_URL=http://127.0.0.1:25321 VITE_SUPABASE_ANON_KEY=<anon> npm run dev` → `http://127.0.0.1:5173` (Node 22 at ~/node22, `npm ci` first if needed).

## Fixture (user + org)

- Create user via `${SUPA}/auth/v1/admin/users` POST `{email, password, email_confirm:true}` with `apikey`+`Authorization: Bearer <service_role>` headers.
- Org: POST `${SUPA}/rest/v1/tenancy_organizations {id, name}` (service key), membership: POST `tenancy_memberships {user_id, org_id, role}` — use **ESTIMATOR** (OWNER triggers aal2/MFA).
- Backend API calls need `Authorization: Bearer <supabase access_token>` + `X-Organization-ID: <org_id>` headers.

## Login (magic-link only — no password form in UI)

1. UI: `/login` → type email → "Enviar Magic Link".
2. Fetch the link from Mailpit: `GET http://127.0.0.1:25324/api/v1/messages` → `GET /api/v1/message/{id}` → regex the `/verify?token=...&type=signup|magiclink` URL → open it in the browser (redirect URL must be allowed or use `token_hash` form).

## Catalog seeding for bow/assembly testing

- Couplers: `profile_articles` rows `role='COUPLER'`, `org_id NULL` — e.g. COPLE-60/COPLE-90 (needs migration 20260922150000 applied or singleton-role CHECK fails; apply via `docker exec -i supabase_db_dekopen psql -U postgres -d postgres -f <file>`; avoid `supabase db reset`, it wipes the fixture org).
- Glass SKUs come from `glass_purchase_mappings.technical_sku` (DEMO_60 has GLASS-BASE). Panel SKUs from `infill_articles` (DEMO_60 has PANEL-SANDWICH-DEMO-24).
- DEMO_60 system_id: `3067da09-3119-5ad0-a1d5-498cd2dfd753` (global demo, quote_ready).
- psql isn't installed on the host — use `docker exec supabase_db_dekopen psql -U postgres -d postgres`.

## Gotchas

- Bow editor: DOOR_ENTRY modules fail evaluation below the door kit's min leaf width (~<700mm) with a generic "no pudo evaluarse" issue; they also need a panel to reach VALID.
- Selecting a profile system in "Vano único" mode then switching to bow locks the editor (pending flag cleared only by classic validation) — switch to bow FIRST, then pick the series.
- UnsavedChangesGuard intercepts Vite hot-reloads mid-edit → "Reload site?" dialogs when files change under you.

## Quotation/documentary flow (emission → artifacts)

- Freeze needs pricing first: "Calcular precio" → "Preparar emisión" → per-position Ubicación + 3 policy selects (fabricación/manillas/refuerzos) → confirm → "Emitir cotización". Requires cost_list_items for EVERY priced SKU incl. kits (KIT-TURN, KIT-DOOR-MULTIPOINT, DEMO-LOCK-MULTIPOINT role=KIT) else 422 cost_list_not_found; cost/pricing tables only RLS-read under pricing_backend role — direct psql INSERT fine.
- Handle intents: `handle_requirement_policies` may require PRIMARY per operable leaf; the prep UI renders per-leaf height + vertical-reference inputs from `handle_requirements` (per policy option, namespaced bay ids like "m2|m2"). Intents can also be PUT directly via `/api/v1/documentary/inputs`.
- Inspector R02: leaf h/w ratio must be in [0.4,2.5] — FAIL blocks freeze regardless of allow_incomplete (only RED/MISSING_INPUT are tolerable, and views.py hardcodes allow_incomplete_workshop=True).
- Inputs seal once a version exists (sealed_documentary_inputs_immutable); version rows can't be DELETE'd without `SET session_replication_role=replica`.
- DOC-03 needs OWNER/WORKSHOP_MANAGER — create a second fixture user (admin API + tenancy_memberships role WORKSHOP_MANAGER; is_active default true). Quote-only versions reject DOC-03 with 422 production_document_blocked.
- Artifact access: POST `/api/v1/documents/artifacts/` {document_type, format, project_version_id} → GET `artifacts/<id>/access/` → signed_url. Supabase returns signedURL relative to `/storage/v1` — that prefix is resolved server-side; if an emitted-artifact link 404s check which revision is running (pre-#43 builds dropped it).
- No poppler/gs on box — open generated PDFs in Chrome via file:// for visual check.

## Merged stack (89d22e0+) extras

- **Job worker required**: artifact generation (DOC-01/03) is now async via the `jobs` queue — the UI polls `/api/v1/jobs/{id}/` forever unless a worker runs: `python backend/manage.py runjobs --poll 1.5` (same env as runserver). No worker = "Generando cotización…" spinner forever.
- **Async artifact open**: the emitted-doc button fetches the artifact and downloads it via an anchor — a post-job `window.open` runs outside the user gesture and gets popup-blocked. If a new open flow ever opens a tab after awaiting, it will hit the same block.
- **Fresh-DB column grants**: `authenticated` has column-level (not table-level) SELECT on `projects`/`project_positions`. New columns added without grants → `GET /projects` 409 `pricing_transaction_rejected` (SQLSTATE 42501). Any migration adding a column to a column-granted table must GRANT it (see 20261020000000 for the projects repair).
- **Fixture API shapes**: POST `/projects/`; POST `/projects/{id}/positions/` `{location_tag,quantity,design:{system_id,nominal_width_mm,nominal_height_mm,color,parametric_tree}}`; POST `/pricing/preview/` `{project_id,pricing_mode:COST_PLUS_MARGIN,context_code:DEFAULT,currency:CLP,effective_date,discount_pct,target_margin,segment:RETAIL,confirmed,reason}` then POST `/pricing/operations/{op}/apply/` `{reason,confirmed:true}`; GET/PUT `/documents/projects/{id}/inputs/`; POST `/documents/projects/{id}/freeze/` `{pricing_operation_id,confirmed:true}`; POST `/production/versions/{vid}/release/` (OWNER/WM only); POST `/production/orders/{oid}/optimize/` `{color}` (required!).
- **Org needs `pricing_rules` row** (`INSERT INTO public.pricing_rules(org_id,pricing_mode,default_margin_pct,tax_rate_pct,waste_factor_pct,labor_rate_per_m2,installation_rate_per_m2)`) else preview 422s `pricing_rules_not_found`.
- **Cost lookup mixes SKUs**: pricing calls `cost()` on purchasing SKU for profiles/steel (DEMO-BAR-*, DEMO-STEEL-BAR-*), but TECHNICAL sku for glass (GLASS-BASE @ M2) and kits (KIT-TURN @ KIT) — seed both forms.
- **workshop_annotations**: ONE record per (bay_id, leaf_id) target — when prep echoes `leaf_id: null`, merge drains+closing+tramo+finish+coupler into the single bay annotation; a second record with the same (bay,null) pair → freeze `Duplicate annotation target` → 422 documentary_authority_required.
- **Priced projects lock positions** — "Duplicar proyecto" needed to edit; demo canvas edits on an unpriced project instead.
- Production optimize UI requires typing a color (placeholder "BLANCO" is not a value) before the button enables.
- **Backend restart hazards**: `manage.py runserver` restarts must verify the old PID actually released :8000 (check log for "port is already in use", kill by exact PID) or the UI silently tests stale code. `supa.env` exports `ANON_KEY`/`SERVICE_ROLE_KEY`/`JWT_SECRET`/`API_URL`/`DB_URL` — map them to `SUPABASE_ANON_KEY`/`SUPABASE_SERVICE_ROLE_KEY`/`SUPABASE_JWT_SECRET`/`SUPABASE_URL`/`DATABASE_URL` or every request 401s and the UI drops to "Acceso tenant no disponible" (expired session → fresh Mailpit magic link).
- **Phase-1 editor surface map**: one registry drives Ctrl+K palette + canvas right-click + toolbar; `+` handles add units; armed split commits at click offset; `wheel` pans the SVG. Native selects may need double-click. Context menu clamps into the viewport — if items clip, the measured-fit regressed. MOCK AI route: same (prompt,product,system) re-Generar replays the audit row — a 500 there is the jsonb `output_payload` decode bug.
