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
