# DEKOPEN — Engineering & Quoting OS for Fenestration

Parametric product engine, 1D cutting optimizer, and commercial quoter for PVC
window/door manufacturers, with `0.00 mm` deterministic tolerance.

## Quickstart

Requires Python 3.12+, Node.js 20.19+/22+, npm. The live DB gate additionally
needs Docker and Supabase CLI 2.116.0.

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
npm ci --prefix frontend

make lint typecheck test build    # unit surfaces
make test-db                      # live gate: clean Supabase stack, pgTAP, RLS, auth e2e
```

Run locally:

```bash
python backend/manage.py runserver          # sqlite fallback without DATABASE_URL
npm --prefix frontend run dev               # Vite dev server on :5173
```

The schema of record lives in `supabase/migrations/`; the deterministic demo
catalog `DEMO_60` lives in `supabase/seed.sql`.

## Development

See [`AGENTS.md`](./AGENTS.md) for the repo map and workflow, and
[`docs/ENGINEERING.md`](./docs/ENGINEERING.md) for the hard invariants
(Decimal determinism, RLS tenancy, immutability, payment idempotency).
Product direction lives in [`docs/PRODUCT.md`](./docs/PRODUCT.md); domain
specifications in [`docs/PRD/`](./docs/PRD/).

Changes land via pull request. CI checks: **Lint & Typecheck**, **Test Suite**,
**Frontend Build**, **Database Gate**.
