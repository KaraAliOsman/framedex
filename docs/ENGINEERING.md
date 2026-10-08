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

## Human codes and exact presentation

Computed values stay exact in the engine, API and sealed snapshots. Formatting
only changes presentation, with half-up rounding where the displayed unit
requires a precision. Use the shared frontend formatters and document renderers.

| Magnitude | Human presentation |
|---|---|
| mm | Integer with thin-space grouping; preserve fractional authority, comma decimal (`1 249,5 mm`) |
| m, m² | Two decimal places (`2,16 m²`) |
| kg | One decimal place (`38,4 kg`) |
| Units | Integer |
| Percent | One decimal place and a space before `%` (`32,5 %`) |
| CLP | No decimals, dot grouping (`$1.435.471`) |
| USD | Two decimals, dot grouping, comma decimal (`US$ 1.234,56`) |
| Angle | Integer unless fractional (`22,5°`), preserving sourced precision |
| Date | `dd-mm-yyyy`, America/Santiago |

Technical CSV/DXF are machine contracts: decimal point, no thousands separator,
unchanged numeric values. Human piece codes are identical in these exports, web,
cut and production PDFs, physical labels and QR. The sheets CSV appends
`piece_label`; all preceding columns retain their positions. PDF text and UI use
the human formats above. IDs in export columns remain machine identifiers.

Projects retain their deliberate global `P-000123` sequence. Purchasing orders,
remnants and receipts use tenant-local `OC-000123`, `RT-000045`, `REC-000012`.
`entity_codes` assigns immutable aliases under a locked transactional counter;
rollback rolls back both the alias and increment. Removed entities keep their
address, so committed numbers are never reused. Backfill orders by `created_at,id`
within organization and kind. Historical order codes, payloads, hashes, issued
artifacts and project numbering remain byte-identical. New purchase orders
reserve their address before sealing. Read projections use the alias only after
checking documentary integrity; existing artifact slots are reused.

Physical codes come from frozen manufacturing identities, for example
`P01-U02-M03`, with reinforcement suffix `-R`; historical `·R` remains accepted
as scan input. They are addresses within their OT: repeated equal cuts consume
distinct frozen identities in deterministic plan order. A QR carries the order,
human code and stable identity, and trace checks all three. It never grants access:
authentication and organization RLS still apply. Presentation fields are copied
onto the read plan, never persisted or included in an engine fingerprint.
Production release creates one OT per position; the twelve-position fixture has
twelve OT. A technical ID is shown only under technical details; a shortened
document/plan fingerprint belongs in the title-block footer.
