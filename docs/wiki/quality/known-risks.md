---
type: risk
status: active
updated: 2026-09-28
volatility: medium
sources:
  - owner conversations through 2026-09-28
  - recent DEKOPEN audit notes
---

# Known risks and audit targets

D04 verifies class expansion, exact sealed mass, component/length picking and
the tenant boundary. Missing machining authority blocks station completion;
synthetic capacity and RC data do not certify a manufacturer. See
[hardware classes](../product/hardware-classes.md). Historical raw work-center
codes and production chrome remain queue work for P12/P13/P16, with full-route
baseline evidence preserved. New hardware controls have their own clean matrix.

This page records recurring failure modes. It does **not** assert that every item is still broken. Re-test against the current ref.

## Editor/domain semantics

- sliders rendered as opening outward;
- slider/casement categories insufficiently separated;
- opening symbols difficult to understand;
- handle side/orientation/3D transform errors;
- bow/bay coupling and angle semantics;
- invalid typology/system combinations;
- visual geometry diverging from engine/product model.

## Direct manipulation/history

- dirty state failing to reset after undo-to-saved;
- unsaved navigation guard behavior;
- pending divider state not clearing;
- divider placement overly center-biased;
- touch divider targeting wrong bay;
- stale listeners after canceled drag;
- top-level/divider limits;
- seam snap outside legal bounds;
- duplicated/unstable positions;
- tree responsiveness;
- coupling target too small;
- handles/controls overlapping dimensions.

## Catalog/authority

- duplicate or conflicting visible role mappings;
- global-vs-tenant authorization mistakes;
- demo data accidentally treated as certified;
- AI import without durable provenance;
- unsupported PDF/image/XLSX claims;
- technical UNKNOWN silently converted into default values;
- imported profile sections with unverified scale/origin/orientation.

D01 adds family guards, exact cut/refinement rules, reviewed import tokens and
append-only publication/retraction history. Its upgrade gate checks old DEMO
products without changing issued authority. Remaining boundaries: scanned images
were pending a verified multimodal route at D01. IA3 later verified real MiMo
vision and bounded scanned-PDF rendering, while literal-evidence and human-review
gates remain. Catalog data stays synthetic until a supplier source is reviewed.
See [the authority page](../product/catalog-authority.md) and
[provider evidence](../product/ai-provider.md).

## Pricing/quotation

- preview mutating persisted state;
- missing cost becoming zero;
- cost and selling price conflated;
- issued revision changing under new catalog/prices;
- unclear successor/reset behavior;
- customer documents exposing internal/confidential cost detail;
- quote UI technically correct but commercially unreadable.

## API/state consistency

- OpenAPI/generated client drift;
- component-local state not persisted;
- background jobs not reflected/refetched;
- retry races;
- confirmation behavior bypassing intended product flow.

## Security

- cross-org onboarding leakage;
- guessed-ID access;
- catalog visibility holes;
- file/document access beyond tenant authority;
- UI-only permission checks.

## Manufacturing

D07 liga la confirmación al diseño y a todos sus marcos; una generación o
timestamp anterior, un actor falsificado o una posición de otro proyecto se
rechazan. Una rectificación después de aprobación exige sucesora, Δ de venta
y confirmación nueva. Los snapshots históricos sin la marca de obligatoriedad
conservan su contrato; las emisiones nuevas no liberan OT pendiente. El borrado
de una posición en borrador conserva su historial inmutable. Las reglas DEMO
no acreditan tolerancias ni montaje reales; deben declararse con fuente por
serie en Ajustes. Véase [vano y montaje](../product/opening-measurements.md).

D03 preserves the R05 structural gate on a tall door with fixed sidelight.
DEMO hardware and a fictional load input do not supply certified inertia or
wind engineering. Never remove the gate to turn an incomplete fixture into a
production order. The legacy upgrade, paired half-cent precision, handle ranges,
catalog retirement and tenant-scoped inspector read have dedicated regressions.
See [physical openings](../product/physical-openings.md).

- released product with incomplete authority;
- BOM and visual product diverging;
- inventory shortage not blocking/flagging correctly;
- remnant/offcut state inconsistency;
- cutting optimization using wrong allowance/stock assumptions;
- remake losing traceability.

## CNC

Treat all CNC capability as high-risk until validated against known machine fixtures.

Audit:

- coordinate frame;
- units;
- face/orientation;
- handedness;
- tool mapping;
- depth;
- clamp collision;
- unsupported operation blocking;
- profile-section orientation;
- deterministic postprocessor output.

Never “best guess” machine data.

## UI/product quality

Audit for features that appear to exist only because they were implemented.

For every control ask:

- Why does it exist?
- What real task does it serve?
- What happens before and after?
- Could the system derive this instead?
- Is the terminology human?
- Is this the right density/hierarchy?

A coherent product matters more than feature count.
