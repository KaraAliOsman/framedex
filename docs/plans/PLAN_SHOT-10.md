# SHOT-10 — Manual quotation workflow

Status: READY_FOR_OWNER_REVIEW.
Base: `6f24fd55768f0ab557cfa314c6cf830d315227fe`.
Branch: `codex/shot-10-manual-workflow`; isolated lead worktree.

## Authorized scope and execution

The Owner approved real project/position persistence, supported rectangular visual
configuration, existing pricing and BOM integration, independent cloning, immutable
revision lifecycle and manual technical catalogs. Ordinary use must require no JSON,
internal IDs, code or manufacturing coordinates. DEMO_60 remains synthetic.

Prior reconnaissance is accepted and reused. The lead is the sole writer; parallel
agents supply bounded build/test patches and independent critique. Pre-existing
SHOT-09 corrective changes remain untouched in the original worktree.

## Minimum implementation DAG

1. Project/position DB boundary and typed API -> list/detail/create UI -> save/reopen proof.
2. Existing engine intent actions -> real S06 hydration/save -> pricing/BOM integration.
3. Technical catalog DB/RBAC -> typed CRUD -> manual UI -> isolation/negative proof.
4. Exact lifecycle compatibility -> independent clone and revision work.
5. Integrated focused proof -> independent adversarial review and real-product
   evaluation -> final canonical Gauntlet -> protected CI -> one PR; no merge.

Nodes 1, 2, 3 and test preparation run concurrently. The lead continuously integrates.

## Authority reconciliation

The semantic catalog gate governs stale screen IDs: systems/profile articles,
glazing-bead compatibility and hardware kits/typed contents. No 3D, Live View,
offcuts/QR, billing or AI capabilities are authorized in this shot.

SHOT-09 snapshots and evidence remain immutable. Existing REV-A authority is not
rewritten. Any missing material lifecycle contract will be recorded as
`[PENDIENTE-DECISIÃ“N]`; independent authorized work continues first.

## Evidence

Implementation checkpoint: `c53ea2b`; SHOT-09 correction integration: `7aaef46`
(incorporates `main @ cee156ea0002f9839645b253a39c88e21a05a28f`). The only
merge conflict was the adjacent SHOT-09/10 roadmap rows; both intended rows survive.
No files in the original working tree were changed by this execution.

Progressive evidence on that implementation plus the working delta described below:

- 54 project/catalog/OpenAPI/document contract tests passed after SHOT-09 integration.
- 61 real PostgreSQL SHOT-10 and SHOT-09 integration tests passed after preserving
  catalog SELECT for the existing pricing/documentary backend roles. RLS predicates
  still constrain own-tenant rows and genuinely global rows; mutation roles unchanged.
- Canonical pgTAP: 8 files / 327 assertions passed on isolated PostgreSQL 17.
- Expanded RLS suite: 141 passed / one fixture incompatibility. The existing
  SHOT-08 zero-draft fixture attributed an ESTIMATOR insert to OWNER. The fixture
  now uses the actual session actor; all four commercial-insert role cases pass,
  and a new real DB regression rejects forged created_by (passed).
- Catalog recovery: 10 component tests passed. Uncertain POST confirmation retains
  the draft and blocks duplicate creation; local validation errors remain retryable.
- Project UI and fixed-result preview: 55 focused component tests passed. Existing
  fixed presentation geometry is reused without new manufacturing formulas.
- Frontend lint/typecheck passed after E2E fixture integration.

Additional progressive evidence (2026-09-19, this working delta):

- Real Chromium project workflow passed: create, configure, save, leave/reopen,
  exact persisted engine result, duplicate, independent draft clone, BOM, invalid
  dimension recovery, failed PUT recovery and unauthorized catalog access.
- Real Chromium hardware-kit create/update/reopen/delete passed, including exact
  Decimal quantities and conditional revision headers.
- Seven auth/canvas/catalog-series browser tests passed together (35.6 s). The
  commercial test now creates and saves the position through the real project GUI,
  applies SHOT-08 pricing and verifies persisted totals after reopening. Series,
  article and bead compatibility creation/update/reopen are verified against DB rows.
- Fixed the explicit demo route's missing dynamic parameters; five focused canvas
  component tests pass against the same static route used by the application.
- Frontend lint/typecheck and production build passed; changed E2E files formatted.
- Catalog editor screenshot reviewed at 1366x768; no material visual defect observed
  on that surface. This is not a full product acceptance verdict.

Closure evidence (2026-09-19, completed execution):
- Canonical Definition of Done Gauntlet (`python scripts/check_dod.py all`): PASS (exit code 0).
  * [1/6] Constitutional source, AST, and semantic hex token guards: PASS.
  * [2/6] Linters and formatting: Ruff, ESLint, Prettier, Orval OpenAPI generator reproducibility check all PASS.
  * [3/6] Strict typechecks: mypy (41 files), django check, tsc --noEmit all PASS.
  * [4/6] Test suites: G-case manifest, golden byte check (read-only), 22/22 mutations killed, engine pytest (244 passed, 5 deferred xfail), backend pytest (320 passed), frontend Vitest (207 passed), and full real Playwright E2E browser tests (all 9 suites passed in 1.1m).
  * [5/6] Frontend production build: Vite build successful (0 errors, 0 warnings).
  * [6/6] Database source and live contract: pgTAP (9 suites, 335 assertions passed), independent PostgreSQL 16 container bootstrap/migration check passed, historical migration upgrade path passed.
- Concurrency & lifecycle test suite (`backend/tests/integration/test_shot10_revision_lifecycle.py`): 4/4 passed. Proves REV-A -> REV-B atomic succession, idempotence, source drift fail-closed, and single successor under high concurrency.
- Product evaluation & adversarial review: Responsive Chilean Spanish quotation workflows, human-readable identifiers, zero hex tokens, strict Decimal invariants, immutable audit persistence (`project_versions`), and complete tenant RLS isolation verified.

## Owner resolutions received 2026-09-19

Project versions are emitted immutable revisions while `projects` and
`project_positions` hold the current editable working revision. Emission changes the
project from DRAFT to QUOTED. OWNER and ESTIMATOR may explicitly reopen a QUOTED
revision as the next deterministic revision (`REV-A` through `REV-Z`, then `REV-AA`,
`REV-AB`, and so on). APPROVED, IN_PRODUCTION, COMPLETED and CANCELLED are not
reopened in SHOT-10. The successor starts from the latest emitted technical state,
fails closed on drift, invalidates live commercial valuation through audited resets,
and requires a new preview, APPLIED pricing operation and explicit emission. Historical
pricing, documentary evidence, purchase projections, requirements and orders remain
immutable and revision-bound.

SHOT-10 introduces additive `SHOT10_V1` documentary authority for REV-A and successor
revisions while preserving historical `SHOT09_V1` evidence and
`DOCUMENTARY_CANONICAL_V1`. New quotation revisions never mutate or silently
supersede prior artifacts or SENT orders.

`project_positions.typology` is derived backend authority. An undivided opening maps
FIXED to FIXED, TURN_LEFT/RIGHT to TURN, TILT_TURN_LEFT/RIGHT to TILT_TURN,
SLIDING_2L to SLIDING_2L, AWNING to AWNING and DOOR_ENTRY to DOOR_ENTRY. Any
horizontal or vertical structural division maps to COMPOSITE. Legacy inputs are checked
against the derived value. COMPOSITE is supported directly by COST_PLUS_MARGIN and
TARGET_GROSS_MARGIN_PROJECT; typology-configured modes require an explicit active
COMPOSITE configuration and fail closed without one. No fallback or invented rate is
authorized.

## Product findings during build

- MATERIAL_FAIL fixed: primary add-position link text inherited the same cyan as its
  background. Scoped primary-action foreground restores readable contrast.
- POLISH fixed: project metadata now uses a compact responsive grid and explicit
  heading hierarchy; no synthetic KPI or decorative chart was added.
- Accurate preview is presently limited to the existing fixed-bay primitive. Other
  supported intent retains an explicitly schematic bay selection, not invented geometry.
