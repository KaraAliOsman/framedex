# SHOT-10 — Manual quotation workflow

Status: final material implementation complete; local Gauntlet PASS on `b78f21f`.
PR remains open for protected CI; Owner authorized merge once its final head is clean.
Base: `6f24fd55768f0ab557cfa314c6cf830d315227fe`.
Branch: `codex/shot-10-manual-workflow`; isolated lead worktree.

## Authorized scope and execution

The Owner approved real project/position persistence, supported rectangular visual
configuration, existing pricing and BOM integration, independent cloning, immutable
revision lifecycle and manual technical catalogs. Ordinary use must require no JSON,
internal IDs, code or manufacturing coordinates. DEMO_60 remains synthetic.

Prior reconnaissance is accepted and reused. The lead is the sole writer; the corrective
pass uses no subagents and one deliberate self-review of its final delta. Pre-existing
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

Historical pre-correction evidence (2026-09-19; does not certify the corrective delta):
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

## Owner corrective contract — 2026-09-19/20

- Missing accessory coverage and glass polishing remain absent. SHOT10_V1 may freeze
  an incomplete commercial quotation with both readiness flags false and no purchase
  projection. Production and purchasing remain fail-closed; historical SHOT09 evidence
  and the strict V1 purchasing model remain unchanged.
- Documentary position inputs require the canonical engine calculation hash at confirmation.
  A changed identity invalidates technical evidence, including same-ID geometry changes.
- Persisted positions reserve their catalog before calculation. Technical catalog rows and
  stock bindings become immutable once referenced; row-version fencing rejects concurrent
  stale saves. New technical authority requires a separate catalog. No saved BOM is rewritten.
- An explicit OWNER/ESTIMATOR reset of an unissued DRAFT retires its live pricing using an
  audited project timestamp. Original APPLIED operations remain immutable. The action binds
  to the expected current operation, clears live amounts, and requires fresh pricing and emission.
- WHITE is the supported API/documentary color. Catalog readiness reports current fixed-white
  prerequisites from backend loaders; it is not design-specific or production certification.
- Node layout reads the existing engine traversal. Split display weights and shortcuts use
  each node's axis dimension; candidate offsets use Decimal hundredth-mm rounding, then strict
  engine validation. Half means 50/50; thirds are distinct commands. Unresolved layouts are schematic.

## Corrective self-review — 2026-09-20

One deliberate review of the corrective delta found and corrected three gaps:
catalog reservation now requires an active editing membership (and OWNER MFA),
fixed-frame readiness resolves the default reinforcement even without an explicit SKU,
and layout responses are bound to organization as well as design inputs.
PostgreSQL reproduced the null-tenant/INSTALLER reservation and missing-default-stock
failures before the fixes; a frontend regression reproduced stale layout across organizations.
Clean migrations and the focused corrective/concurrency/revision suites passed (24 tests),
as did the layout/editor regression tests (8 tests). Canonical closure evidence follows separately.

Gate-driven corrections preserve legacy APPLIED operations without approval timestamps
when no pricing reset exists; after reset, only a newer approval is current. The unchanged
SHOT-09 pgTAP contract proves historical compatibility. Mutable catalog permission fixtures
now use independent unreferenced catalogs, preserving all 335 pgTAP assertions. Project E2E
uses the complete canonical synthetic catalog; catalog CRUD keeps its independent tenant copy.

Local Windows Docker recovery: the interrupted Desktop had stale AF_UNIX socket directories
in `%LOCALAPPDATA%/Docker/run` and `%LOCALAPPDATA%/docker-secrets-engine`. Stop the identified
Desktop/backend processes, preserve both directories under unique sibling backup names,
verify both original paths are newly created and empty, then launch the installed Desktop
from `%LOCALAPPDATA%/Programs/DockerDesktop`. Verify `docker info` before Supabase. This
recovered Linux engine 29.7.2 without deleting volumes or resetting Docker data. Socket
backups contain runtime endpoints, not a repository dependency; retain them for diagnosis.

## Final corrective verification — 2026-09-20

`python scripts/check_dod.py all` completed with real exit code 0 on the implementation
tree committed with this record: constitutional guards, Ruff, ESLint, Prettier, reproducible
OpenAPI/client generation, mypy (43 files), Django checks, TypeScript and production build.
Engine: 248 passed plus 5 existing deferred xfails; backend: 345 passed; frontend: 213 passed;
real Playwright: 9 passed; pgTAP: 335 assertions across 9 suites. PostgreSQL lint found no
schema errors; independent PostgreSQL 16 bootstrap and populated historical upgrade passed.
Golden byte check remained read-only and passed; 22/22 core mutations were killed. No
checker logic, workflow protection or Golden artifact was changed. Mutable test fixtures
were isolated without removing assertions. No implementation changes followed that run
until the final Owner-directed review below.

## Final Owner-directed review — 2026-09-20

The persisted quotation API exposed FOILED on project positions and documentary finish
inputs even though ordinary project options, the adapter and SHOT10_V1 emission support
WHITE only. Normal project saves rejected FOILED before persistence, but the advertised
contract was inconsistent and documentary inputs could persist a value that emission
would reject. Commit `4e1b7d1` introduced a WHITE-only enum for persisted project
request/response, legacy pricing-draft persistence and documentary annotations. Generic
engine and inspector color types retain FOILED capability; no engine formula or generic
storage contract was narrowed.

The final protected review then reproduced two additional defects: an APPLIED draft could
be repriced without the explicit audited reset, and concurrent singleton profile-role
writes could both pass the service precheck. Commit `2fe7f01` blocks replacement previews
until the current authority is reset, serializes singleton-role create/update decisions and
adds tenant/global partial unique indexes for database enforcement. Commit `4fa5f55`
preserves the historical unapplied-freeze negative proof under that stricter lifecycle.
Protected CI then reproduced package-level XLSX nondeterminism: OpenPyXL overwrote the
fixed modified timestamp during its convenience save. Commit `b78f21f` uses the same writer
without that timestamp mutation and makes the differing-clock regression deterministic.

Focused proof: 114 pricing/catalog/corrective/revision integration tests, 69 related unit
contract tests, 24 SHOT-09 documentary integration tests, 11 document contract tests and
337 pgTAP assertions passed; Ruff and PostgreSQL lint also passed. The canonical Gauntlet
then passed on final material head `b78f21f66cab530a20473c271d9e37e3ba600488`
with exit code 0: 248 engine tests plus 5 existing deferred xfails, 349 backend tests, 215
frontend tests, 9 real Chromium
suites and 337 pgTAP assertions. Golden remained read-only, 22/22 mutations were killed,
PostgreSQL 16 clean bootstrap and historical upgrades passed, and the production frontend
build completed without warnings. No executable change followed this run.
