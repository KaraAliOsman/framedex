---
type: state
status: active
updated: 2026-10-05
volatility: high
verified_ref: a096f85b2e56e21eda024c1ec92a456ed9d30b03
sources:
  - repository main
  - P00 foundation PR #114
  - integracion/v1 merge a096f85b2e56e21eda024c1ec92a456ed9d30b03
  - open PR metadata observed 2026-09-27/28
  - AGENTS.md
  - docs/PRODUCT.md
  - docs/ENGINEERING.md
---

# Current reality

**Warning:** this is a volatile navigation page. Re-check the repository before relying on it for implementation decisions.

## Verified repository baseline

At the verification ref (`a096f85b2e56e21eda024c1ec92a456ed9d30b03` on `integracion/v1`), the repository identifies DEKOPEN as:

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

## IA1 AI evaluation harness and baseline diagnosis

The IA1 encargo added a result-based AI evaluation harness under `backend/ai_gateway/evals/` (runnable via `make test-ai-evals` or `python scripts/ai_evals.py`): 26 YAML cases drive the real UI routes (`design_assist.assist`, `agent._act`, `assist.ask`) in-process with only I/O edges patched, apply proposed ops through the real frontend `applyDesignOps` reducer bundled via esbuild into a Node sandbox, and score the resulting product structure (mm measures, openings, glass SKUs) — never the reply text. A deterministic 10-category failure taxonomy classifies each miss. Committed baselines live in `docs/ai/evals/` (`2026-10-05-mock.json`, `2026-10-05-mimo.json`) with the diagnosis in `docs/ai/evals/README.md`; CI runs the MOCK suite in the non-blocking `AI Evals (MOCK, non-blocking)` job.

Baseline findings (2026-10-05, ordered by impact — verified file:line evidence in the README):

1. The configured real provider (MIMO) answers HTTP 429 `ai_provider_quota` on every call — all AI surfaces are down in production today.
2. `design_assist._summary` requires a flat `product["modules"]` list (`design_assist.py:103-115`), but agent batch ops load the persisted `parametric_tree` (`agent.py:761`) — every stored position is rejected `unsupported_product`: project-level batch ops are structurally broken.
3. The ops vocabulary covers only adjustments — no bay-split, position-create/duplicate or hardware ops; worse, `SLIDING_2L` is a valid `OPENINGS` value so a sliding conversion validates and applies on an incompatible system.
4. Context projections lack sash weight, engine validation blockers, per-position prices, version diffs and cut-plan bars — honest answers reduce to "sin dato".
5. `_declared_values` accepts only literal numbers — relative-measure instructions ("20 cm más ancha") are impossible, while absurd literal values pass range checks.

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
