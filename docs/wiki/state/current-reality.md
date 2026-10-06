---
type: state
status: active
updated: 2026-10-06
volatility: high
verified_ref: 407f4ffd609a2dd4536e3e3c765eb7117c69715f
sources:
  - repository main
  - P00 foundation PR #114
  - local stack fixes PR #116
  - P01 local gates and browser evidence, 2026-10-05
  - IA1 rollback harness and dated outcome evidence, 2026-10-05
  - D01 catalog authorities, interchange and browser evidence, 2026-10-05
  - D02 glass recipes, persisted quotation/orders and browser evidence, 2026-10-05
  - integracion/v1 merge a096f85b2e56e21eda024c1ec92a456ed9d30b03
  - open PR metadata observed 2026-09-27/28
  - AGENTS.md
  - docs/PRODUCT.md
  - docs/ENGINEERING.md
---

# Current reality

## D02 glass composition verified 2026-10-06

The D02 branch adds structured exterior-to-interior recipes, sourced properties
and safety rules, exact Decimal mass/minimum-area/process pricing and immutable
catalog identities. The upgrade adds composition metadata without rewriting saved
BOMs, issued revisions, price history or document hashes. Unknown legacy notation
and missing PVB data remain explicitly unknown.

The selector and compositor use the same typed operation and engine as persisted
positions. Real browser verification covers alternatives on the affected bay,
undo/redo, publication with a reviewed diff, save/reopen and the five states.
Thirty-six screenshots have no text/presentation findings within the new glass
surface, no overflow and no browser errors. Settings has no findings in either
theme; inherited editor/production findings remain assigned to P04/P12/P13.

A real twelve-position project passes pricing, freeze, DOC-01, production release
and supplier PDF/CSV downloads. Twenty-four labels and all cut dimensions match
the frozen BOM. PDFs use bundled Plex fonts on Windows. New DEMO documents mark
every page, including a synthetic glass recipe on a commercial system; already
issued files remain immutable. The current template has ten sheets, including
Glass rules; the D01 nine-sheet evidence below describes its historical version.

The official NCh 135/2 rules and supplier thermal/security properties remain
owner-provided data. Empty rules and reviewed DEMO examples are not certification.
The clean Database Gate passes 959 pgTAP assertions, 280 integration tests and
11 Chromium flows, PostgreSQL 16 and populated upgrades. Legacy writes remain
subject to mandatory safety rules and structured SKUs require their complete
recipe. The published fixture now consumes exact catalog tariffs and separates
glass purchasing units from its m² pricing contract. Supplier PDFs repeat the
DEMO warning on every page, using the shared documentary running header.
See [D02 acceptance](../../redesign/captures/vidrios-compuestos/aceptacion.md),
[glass authority](../product/glass-composition.md) and
[activation](../../operations/ACTIVACION.md). D03–D07 and subsequent product
surfaces still require their own acceptance.

D02 is integrated through PR #120 at the verification ref. All four required
GitHub checks passed on `f53b66db4e30640a6e0440bbb2b82507aa6a3b6d` in run
37409956027: Lint & Typecheck, Test Suite, Frontend Build and Database Gate.

## D01 catalog authority verified 2026-10-05

The D01 branch separates five system families, adds exact per-profile cut and
reinforcement rules and sourced dimensional limits, and supplies five explicitly
synthetic DEMO series with reproducible costs. New products use family compatibility;
the upgrade preserves historical saved calculations and issued documentary authority.

Manual nine-sheet import and real MiMo text extraction converge in source-backed
review, a transactional diff, explicit publication and guarded undo. Original
evidence survives reviewer corrections. No PDF candidate was published during the
real-provider verification. The measured source produced 31 candidates, 324 supported
HIGH fields and 27 UNKNOWN fields. Scans without text remain an explicit limitation.

All five new DEMO series are quote-ready through the same authenticated catalog
discovery used by the editor. The readiness check consumes their declared cut and
reinforcement rules, including sliding sash mass and rail authority. Local unit
gates pass, as do 936 pgTAP, 274 integration tests and 11 Chromium end-to-end flows.
The complete clean Database Gate also passes independent PostgreSQL 16 and all
four populated-upgrade verifiers. D01 is integrated through PR #119 at the
verification ref. All four required GitHub checks passed on
`28509e69c23b871451502fc147c552475d9f3238` in run 37393755094, including
the expanded 28/28 formula mutation drill. `main` is unchanged.

Verification details and the acceptance scope are in
[the D01 report](../../redesign/captures/sistemas-catalogo/aceptacion.md) and
[the durable catalog page](../product/catalog-authority.md). D03–D07 and P16 still
need their own acceptance; this does not accredit unfinished queue surfaces.

**Warning:** this is a volatile navigation page. Re-check the repository before relying on it for implementation decisions.

## IA1 outcome measurement verified 2026-10-05

The rollback-only local evaluation harness runs the 26 owner requests through the real agent endpoint, handler and job read. Proposed commands apply to copies via the canvas registry and the engine, with exact structural oracles and persistent-state checks. The dated MOCK/real-provider results and root causes are in [the baseline report](../../ai/evals/README.md); this acceptance measures the AI and does not claim that its failing capabilities were repaired.

MOCK repeated the same 26 verdicts and structures. The local fixture has no applied prices, emitted A/B revisions or optimized OT; missing authority remains explicit. Browser evidence reproduces completed jobs with rejected operations and no saved design. IA2/IA3 must address these behaviors against the same outcome suite. No provider credential, public API, production prompt, operation vocabulary or engine formula changed in IA1.

The final baseline is MiMo 3/26 and MOCK 0/26. E03, F01 and G02 pass, with F01 limited to the real empty order list. Both reports verified unchanged persistent state and source. Graph scores require engine acceptance; compatibility refusals require catalog authority, duplication requires bedroom destinations, and existing applied prices/cut plans are loaded when present. The 48 oracle regressions include rejection of false glass offers, missing installation questions and contradictory handedness. The PostgreSQL observer regression passed after a clean-stack rebuild.

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
