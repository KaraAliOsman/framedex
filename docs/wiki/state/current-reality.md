---
type: state
status: active
updated: 2026-10-05
volatility: high
verified_ref: 023b8ba303b680ca50b6e10119ce4ee4514c9c38
sources:
  - repository main
  - P00 foundation PR #114
  - local stack fixes PR #116
  - P01 local gates and browser evidence, 2026-10-05
  - integracion/v1 merge a096f85b2e56e21eda024c1ec92a456ed9d30b03
  - open PR metadata observed 2026-09-27/28
  - AGENTS.md
  - docs/PRODUCT.md
  - docs/ENGINEERING.md
---

# Current reality

**Warning:** this is a volatile navigation page. Re-check the repository before relying on it for implementation decisions.

## Verified repository baseline

At the verification ref (`739704ab8f81ded8f860d44d44adba0c33f96db4` on `integracion/v1`), the repository identifies DEKOPEN as:

- a pure deterministic engine under `engine/`;
- Django modular monolith under `backend/`;
- React + TypeScript + Vite under `frontend/`;
- Supabase/Postgres migrations and RLS under `supabase/`;
- product/engineering specifications under `docs/`.

Hard invariants documented by the repo include:

- Decimal for millimetres/money;
- no LLM/free-text numeric engineering truth;
- 0.00 mm deterministic golden behavior;
- tenant `org_id` + RLS;
- immutable issued artifacts/history;
- explicit human action for externally consequential events.

## Product direction already present in the repo

`docs/PRODUCT.md` already encodes:

- unified product-centered workspace;
- compositional assemblies/modules/couplings;
- bow/bay as templates over composition rather than enum branches;
- direct manipulation + typed operations + undo/redo;
- AI using the same typed operations as UI;
- workshop-language validation;
- Oknosoft/WindowBuilder as a domain reference.

## P00 foundation state

P00 is merged in PR #114 and adds the v1 integration foundation:

- `integracion/v1` exists as the queue integration branch.
- `docs/design/CONSTITUCION.md` is the mandatory design constitution copied from the queue.
- `docs/decisions/valores-por-defecto.md` records constitution defaults for later implementation.
- `docs/operations/ACTIVACION.md` indexes deferred external integrations without secret values.
- `frontend/scripts/ux-capture/` provides a Playwright capture harness with text/presentation detectors and unit coverage.
- The production route table hides `/projects/demo/positions/g1/edit` behind the same dev-only mechanism as `/benchmark`.
- `scripts/dev_fixture.py` now seeds more realistic DEMO fixture identity, clients and project volume while preserving `DEMO_60` as synthetic reference data.

Verification caveat: PR #114 passed the required GitHub checks (Lint & Typecheck, Test Suite, Frontend Build, Database Gate). Its local notes still state that Windows policy blocked `rpds` during generated-API drift checking, and the committed baseline capture is a smoke baseline for `/login`; later queue items must run the full route matrix once portal tokens and all fixture states are available.

## Local stack fixes verified 2026-10-05

PR #116 is merged at the verification ref and carries the four former local-only commits. The fixture preserves prepared workshop evidence, declares its synthetic handle intent against the leaf datum, and respects sealed inputs on repeats. The PowerShell launcher withholds environment values and cleans up only its own processes on failure.

All four local make gates passed, including OpenAPI/orval reproducibility; the earlier `rpds` limitation did not recur. Required GitHub checks passed on PR #116. Docker Desktop fails to initialize its ingest socket; an isolated local WSL test daemon now runs the Supabase verification stack without deleting the Desktop data. This environment recovery does not establish any product capability as accepted.

## P01 design material verified 2026-10-05

P01 supplies the constitution tokens, self-hosted IBM Plex fonts, Decimal-safe presentation, exhaustive generated-enum labels, Spanish form validation and reusable UI primitives. `/dev/ui` is development-only and reads project/BOM data through the authenticated API. Source guards ratchet against a committed baseline; live detectors preserve inherited findings instead of accepting them as compliant.

The four local make gates passed with 472 engine tests (two expected failures), 1,058 backend tests and 697 frontend tests. The manual passed 22 theme/density/viewport combinations with no serious or critical axe findings, including errors and dialogs. Spanish validation passed four real Catalog/Payments flows with zero invalid API writes. Three canvas E2E flows passed with exact grouped dimensions, visible outline focus, transactional rollback and paint times below 300 ms. The 352 before and 352 after route captures have no increased detector count in any combination and no new horizontal overflow.

The migrated legacy CSS, including import entrypoints, shrank from 5,357 to 3,750 lines (30.00%). Including 792 lines of new primitive styles, the complete scoped graph has 4,542 lines (15.21% net reduction). See `docs/redesign/captures/sistema-diseno/aceptacion.md` for the scope, editorial rubric and evidence.

Limits remain explicit: position responses do not provide the complete formula/input/engine-version trace; the trace component exposes its absence. Portal capture references exercise error states rather than five issued quotations. Product surfaces later in the queue still have inherited findings and are not accredited by the P01 material acceptance. P01 is merged in PR #117 at `023b8ba303b680ca50b6e10119ce4ee4514c9c38` with all four required GitHub checks passing.

## Recent branch/PR caution

The repository has accumulated many historical branches and stacked agent changes.

Do not assume “latest PR number = complete product”.

As of the latest observed metadata around 2026-09-27/28, PRs including #107 and #109 were open; their relevance/current CI must be checked again before use.

Historical audit notes reported periods where:

- commercial-workspace work existed on a large advanced branch;
- OpenAPI/client drift and catalog authorization defects blocked CI;
- documentation/testing PRs were not substitutes for missing product stabilization.

Treat these as leads for inspection, not timeless truth.

## Current-state procedure

Before changing a capability:

1. locate current implementation on the target ref;
2. inspect related migrations and generated API types;
3. inspect recent PRs/branches that may supersede main;
4. run focused tests;
5. use the real UI if behavior/UX is involved;
6. then update this page if a durable current-state fact materially changed.

A fuller capability-by-capability reality map should be added only after a fresh systematic repository + running-product audit.
