# DEKOPEN — repository map

DEKOPEN is a parametric engineering + quoting OS for PVC/aluminium fenestration:
a deterministic pure engine, a Django modular monolith, Supabase/Postgres with RLS,
and a Vite + React SPA.

## Layout

- `engine/src/dekopen_engine/` — pure calculation engine. No I/O, no Django, no HTTP.
  All dimensions and money are `Decimal`; tolerance is `0.00 mm`.
- `engine/tests/` — engine tests incl. golden cases (`test_gold_cases_*`) that freeze
  proven manufacturing math.
- `backend/` — Django apps by domain (`authentication`, `engine_api`, `projects`,
  `pricing`, `documents`, `purchasing`, `billing`, `catalogs`). HTTP edge only;
  numbers come from the engine.
- `frontend/` — React 18 + TypeScript + Vite. Product UI lives in `src/features/`.
  API client is generated from `backend/openapi.yaml` (orval).
- `supabase/` — migrations (source of truth for schema), `seed.sql` (canonical
  `DEMO_60` demo catalog), pgTAP tests.
- `docs/PRD/` — domain specifications. `docs/ENGINEERING.md` — hard invariants.
  `docs/PRODUCT.md` — product direction.

## Working here

Start with the current task and ref:

1. Inspect `git status --short` and the current branch; preserve other work.
2. Use the domain routes in `docs/wiki/index.md` to select source directories,
   tests and relevant specifications. Read linked knowledge when it informs the
   task; do not load the entire wiki, PRD collection or chronological log.
3. Search those directories with `rg` before expanding the scope. Use
   `rg --files <directory>` for discovery and a symbol/error search for detail.
   API changes start in backend views/serializers; regenerate OpenAPI and orval
   output instead of editing `frontend/src/api/generated/` by hand.
4. Check claims against the target code/ref. Earlier mandates, acceptance
   reports, captures and raw research were retired on 31-10-2026; they live in
   Git history at `588e6332` and are not assignments. Current owner
   instructions and `docs/dekopen3/PLAN.md` govern the task; the UI authority
   is `docs/design/CONSTITUCION.md`.

The normal loop: understand → implement → exercise the affected capability →
fix what is wrong → continue. Verify the surface you touched; run the full suite
when the change is genuinely cross-cutting.

```text
make lint           # ruff, ESLint, prettier, generated-API sync, source guards
make typecheck      # mypy engine/, Django check, tsc
make test           # engine + backend unit + frontend unit tests
make test-db        # live Supabase gate (needs Docker + supabase CLI): pgTAP, RLS, auth e2e
make test-mutations # 0.01mm formula mutation drill
make build          # production frontend build
```

Local product review (roles, worker and real AI): `scripts/start_local.ps1`,
documented in `.agents/skills/testing-framedex/SKILL.md` and `docs/GUIA-REVISION.md`.
Reuse an owner's running stack when the task needs its existing state; starting
REVIEW rebuilds containers and runs the fixture. Code changes are not hot-reloaded
into its built images. Ordinary documentation work needs no stack startup.

Development servers: `npm --prefix frontend run dev` and
`python backend/manage.py runserver`. Django uses sqlite without `DATABASE_URL`;
real tenancy requires Supabase/Postgres.

## Hard invariants — see docs/ENGINEERING.md

- Engine output is the only source of computed numbers. Never let free text,
  templates, or an LLM manufacture a numeric result.
- `Decimal` for mm and money — in engine, backend, and SQL (`NUMERIC`, never float types).
- Every tenant table keeps `org_id` + RLS; cross-tenant reads are bugs, not features.
- Issued revisions/documents and price/audit history are immutable.
- Payments are idempotent; externally consequential actions require an explicit
  human click.
- Formula changes ship with a golden-case test. Regenerate goldens only via
  `make goldgen` and review the diff.
- UI: `docs/design/CONSTITUCION.md` is mandatory for product surfaces.

## Commits and PRs

Changes land via pull request. CI jobs (Lint & Typecheck, Test Suite, Frontend
Build, Database Gate) are the merge safety net — fix what they flag, don't weaken
the checks.

## Persistent project knowledge

DEKOPEN keeps a maintained LLM Wiki under `docs/wiki/` so project decisions,
research and cross-session synthesis do not disappear into chat history.

For tasks that depend on project history, owner intent, known risks, competitor
research or prior conclusions:

1. read `docs/wiki/index.md`;
2. read the relevant linked pages;
3. for current implementation claims, re-check the target ref/code/tests/running
   product — the wiki never overrides newer repository evidence;
4. when work produces durable knowledge, maintain the wiki according to
   `docs/wiki/SCHEMA.md` and append `docs/wiki/log.md`.

Keep four categories distinct: verified current repo fact, owner/product intent,
historical context, and external research. Never turn a wiki inference into
engineering numeric truth or production authority.

## Repository hygiene

Read `docs/operations/WORKSPACE.md` before cleaning local files. `.run/` also
holds persistent browser sessions, stack ownership and registered WSL storage.
Keep generated captures, screenshots and run logs in `.run/`; the repository
holds code, tests, fixtures and the documents that describe the current product.
`.rgignore` keeps broad discovery focused by omitting generated API/schema,
golden JSON payloads, eval payloads and the chronological log.
These files remain available: open a known file directly or use
`rg --no-ignore <pattern> <specific-directory>` for a scoped investigation.
Search exclusions do not change Git tracking, builds or test inputs.
