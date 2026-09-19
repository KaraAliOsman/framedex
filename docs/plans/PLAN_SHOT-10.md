# SHOT-10 â€” Manual quotation workflow

Status: BUILD IN PROGRESS. Owner functional contract received 2026-09-18.
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

These are progressive checks, not SHOT closure. Independent adversarial review was
interrupted by the subagent usage limit and produced no verdict. No canonical final
Gauntlet, protected CI or PR yet. Material gaps below still prevent full acceptance.
The local stack is isolated as `dekopen-shot10` on 26321/26322, preserving the original
`dekopen` runtime. Synthetic test copies are explicitly labeled and never production data.

## Material decisions still absent from the active authorities

`[PENDIENTE-DECISIÓN]` Revision successor and state machine. PRD-02 enumerates statuses;
the roadmap requires editing an emitted revision to produce REV-B. SHOT-09 PD-09-01
and its temporal contract define only REV-A. Exact transition permissions/preconditions,
successor source and treatment of applied pricing/documentary inputs are not specified.
Current implementation preserves immutable history and blocks edits after freeze or
applied pricing. Draft-only cloning is independent and verified; emitted-project cloning
and successors are not claimed complete. No material rule has been invented.

`[PENDIENTE-DECISIÓN]` Pricing classification of a divided position. The engine accepts
supported split intent, while SHOT-08 commercial configuration is keyed by position
`typology`. The existing specification does not assign that commercial key to mixed
or divided designs. The API currently rejects saving them with a domain error rather
than silently reclassifying them or emitting an ungoverned price. This is an outstanding
hard-gate gap, not a completed configurator capability.

## Product findings during build

- MATERIAL_FAIL fixed: primary add-position link text inherited the same cyan as its
  background. Scoped primary-action foreground restores readable contrast.
- POLISH fixed: project metadata now uses a compact responsive grid and explicit
  heading hierarchy; no synthetic KPI or decorative chart was added.
- Accurate preview is presently limited to the existing fixed-bay primitive. Other
  supported intent retains an explicitly schematic bay selection, not invented geometry.
