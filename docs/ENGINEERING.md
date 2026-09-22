# DEKOPEN — engineering invariants

Short list of guarantees that protect real damage. Everything else is ordinary
engineering judgment — component structure, naming, CSS, internal APIs, reversible
architecture. Don't escalate those.

## Numbers and determinism

- `/engine` is pure: no I/O, no Django, no HTTP, no `float`. Test it with
  `pytest engine/`.
- Every computed dimension/weight/price comes from the engine or from an explicit
  human-entered field — never from free text, templates, or an LLM.
- `Decimal` for millimetres and money everywhere: engine, backend serializers, SQL
  (`NUMERIC`, never `REAL`/`FLOAT`/`DOUBLE PRECISION`). Tolerance is `0.00 mm`.
- Formula changes ship with a golden-case test (`engine/tests/test_gold_cases_*`).
  Regenerate goldens only via `make goldgen` and review the diff.
- The deterministic golden cases (G1–G7 and successors) describe proven
  manufacturing behavior — keep them passing at `0.00 mm`.

## Data and tenancy

- Schema of record: `supabase/migrations/`. The canonical demo catalog `DEMO_60`
  lives in `supabase/seed.sql` — synthetic, never a certified catalog.
- Every tenant table: `org_id` + `ENABLE ROW LEVEL SECURITY` + policies through
  `private.current_user_org_ids()`. A cross-tenant read is a release blocker.
- Global catalogs are world-readable; tenant data never is.
- Issued artifacts are immutable: project revisions, emitted documents, price and
  audit history, BOM snapshots. Corrections happen in a new revision.
- Migrations must apply cleanly on populated data and reject invalid upgrades
  atomically (`make test-db` exercises both on real Postgres).

## Money and externally consequential actions

- Payments are idempotent: replays, out-of-order callbacks, and retries never
  double-charge or double-grant.
- Sending to a customer, releasing to the factory, and purchasing material each
  require an explicit human action. No silent irreversibility.
- AI writes are audited before they are applied (`ai_audit_logs`).

## Product judgment

- Users see workshop language: what is wrong, why it matters, what it affects,
  how to fix it — never enum names, hashes, IDs, or stack traces.
- Distinguish "geometry valid" from "manufacturing definition incomplete"; never
  pretend missing catalog authority is exact output.
