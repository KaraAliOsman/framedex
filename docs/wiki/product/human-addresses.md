---
type: concept
status: active
updated: 2026-10-07
volatility: medium
sources:
  - supabase/migrations/20270107000000_human_entity_codes.sql
  - backend/production/pieces.py
  - backend/tests/integration/test_human_codes.py
  - docs/redesign/P02-ACEPTACION.md
---

# Human addresses without rewriting history

P02 adds tenant-local OC/RT/REC aliases with independent transactional counters,
RLS and immutable assignments. Deterministic backfill sorts timestamp and UUID.
Historical source orders, receipt/remnant rows and documentary fingerprints are
preserved. New OC reserve the same code that gets sealed. The populated PG16
upgrade verifier compares every source row before/after the migration.

Physical codes derive from sealed manufacturing facts and allocate repeated
equal specs to distinct stable identities. Web, cut/production PDF, CSV, DXF,
labels and QR share the same read-only projection. Presentation fields never
reach strict engine models or optimization fingerprints. `-R` denotes the
reinforcement; historical `·R` is accepted when scanning.

Planned placements reconcile across saw web/PDF/CSV/DXF/labels. The full
production bundle also names frozen pieces without a stock/cutting solution;
those references remain explicit and never acquire invented CNC coordinates.
The unit QR verifies its own order-and-unit identity instead of comparing it
with an individual member identity. SVG viewBox and four-module quiet zones
preserve actual scanning at small sizes. Pixel decoding covers eight screen
labels, 24 workshop PDFs and four browser printouts; dark print uses paper/ink.

Ctrl+K resolves OC, REC, RT and OT to their entity. Purchase and receipt searches
use the same documentary authority and role limits as purchasing; operator and
installer searches do not expose commercial data. A piece QR binds order, code
and identity, and works by navigation or by pasting into the scanner. The link
does not bypass authentication or RLS. Unknown/cross-organization addresses show
the missing state. See [format and identity contracts](../../ENGINEERING.md).

Current evidence is a synthetic DEMO fixture, with twelve positions released as
twelve OT, containing 646 physical codes. This verifies artifact reconciliation,
not a real manufacturer's dimensional certification. The broad purchasing and
production screens retain their historical layout for P11/P12/P13; P02 changes
formatting, identity navigation and the asynchronous states it exercises.
