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

## Branch switching + shared-tree hazards

- runserver uses `--noreload` — after `git checkout` of a new branch, RESTART Django or it serves the old commit (symptom: new API fields like `handle_requirements` missing). `/tmp/supa.env` exports `API_URL` (not `SUPABASE_URL`) — Django needs `SUPABASE_URL=$API_URL` else all tokens 401 `invalid_token`.
- `pkill -f "manage.py runserver"` matches your OWN shell command line and kills it — use `pgrep -f 'manage[.]py'` + `kill` instead. Start detached: `setsid nohup <script> >log 2>&1 </dev/null &`.
- Shared checkout may carry the lead's UNCOMMITTED WIP — check `git status --short` before backend restarts; a dirty `options.py`/`ProductFrontSvg.tsx` broke design-options (500 `.name`) and Vite builds (parse errors) mid-run. Workaround for backend: `git worktree add /tmp/wt-<sha> <sha>` and run manage.py from there; for the frontend there's no clean isolation — retry transient parse errors, or bypass the editor by creating positions via `POST /api/v1/projects/{id}/positions/` (product-v2 tree JSON, returns 201+BOM) and test the doc-prep UI from the project page.
- Date `<input type=date>` fills need a click ON the mm segment then digits only (09→23→2026 auto-advances); typing slashes or a focused omnibox leaks text into the address bar.
- R09/R07/R08 inspector rules gate documentary_complete: per-bay `workshop_annotations` need finish_class+continuous_width_mm+has_coupler (R09), bottom_drain_holes_mm (R07), closing_points_perimeter_mm (R08) — no UI editor for any of them; a UI-only emission always seals "Evidencia de diseño" even with handles filled via UI.

## Workshop inputs UI (branch workshop-inputs / later)

- "Datos de taller" collapsed `<details>` inside the position fieldset in "Preparar emisión" — per-bay Desagües inferiores (CSV mm), Tramo continuo, Acople de dilatación (Sí/No select); per-leaf Puntos de cierre (CSV mm, closing positions around leaf perimeter); per-span Exigencia estructural (Ix cm⁴ + Base de cálculo — only rendered when spans exist); per-glass Cantos pulidos select (Pendiente/Sin pulido/Con pulido — "Con pulido" reveals Superior/Derecha/Inferior/Izquierda edge checkboxes); Accesorios Cobertura select. Every unanswered control shows a "pendiente" chip.
- NO save button — "Emitir cotización" PUTs `/documents/projects/{pid}/inputs/` with all in-memory fields then POSTs `freeze/` atomically. A page reload loses unsaved edits (verify unsaved state is gone after F5 before re-typing).
- Inspector value checks (NOT just presence): R07 needs `bottom_drain_holes_mm` count ≥ required_bottom_drains for bays wider than width_trigger (DEMO_60: ≥3 holes for bays >800mm); R08 needs closing-point gaps ≤ max_spacing_mm (DEMO_60: 800mm) around the leaf perimeter (~4184mm for a 796×1296 leaf → ~6 points). Sparse-but-present values → FAIL → 422 `inspector_red_blocks_documentary_freeze`. The UI surfaces NO field-level error — diagnose via DB: `snapshot_json->'inspector'` on project_versions (after emit) or reproduce `dekopen_engine.inspector.inspect` in a Django shell (`config.settings`, tables `project_positions` + `position_documentary_inputs`).
- "Evidencia completa" = documentary_complete=true AND production_allowed=true → DOC-03 generatable (WM role). "Evidencia de diseño; faltan antecedentes de producción" = design-only → DOC-03 → 422 `manufacturing_document_incomplete`. Assemblies (product-v2) always force both false — quote-only by design.
- Labels: classic positions show "Vano N"/"Hoja N"/"Vidrio N"/"Travesaño N · X mm"; assembly targets namespace `<module_id>|<id>` — known leak: leaf labels use raw module id ("Unidad m2 · hoja 1") while bays/glass use ordinals ("Unidad 1 · Vano 1").
- Fixture shortcuts: project/position creation via POST `/api/v1/projects/` + `/projects/{id}/positions/` is faster than the editor for repeat fixtures (TURN_LEFT tree: `{"type":"BAY","opening_type":"TURN_LEFT","glass_thickness_mm":"4.00","glass_spec":"4.00","glass_article_sku":"GLASS-BASE"}` — but note a saved UI-built position folds to this same shape; position ids like `00000000-0000-4000-8000-0000000000aa` work).
- The split-position (Dividir en horizontal) produces a travesaño span target → structural editor appears; R12 is NOT_APPLICABLE for spans <4500mm so Ix/base are optional-but-stored (target_id "m1-sh1" = module-prefixed sash/sash-horizontal id).
