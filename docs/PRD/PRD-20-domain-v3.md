# PRD-20 — Domain V3: contours, paths, connections

Phase-2 domain evolution. DEKOPEN moves from "rectangular parametric modules
joined linearly by couplings" to "general fenestration design platform" —
without discarding the proven compositional model.

**Invariants preserved:** engine-only computed numbers; `Decimal` mm;
0.00 mm tolerance; immutable sealed documents; honest UNKNOWN catalog data;
one typed command/registry layer for human + AI edits.

## 1. Target model mapped onto today's schema

| Mandate concept | V2 reality | V3 evolution |
|---|---|---|
| Product | `ProductModel` (`product-v2`) | unchanged envelope; `product-v2` stays the wire version (additive fields) |
| Assembly | `CoupledAssembly` modules+couplings | unchanged container; connection kinds extend `CouplingDef` later |
| Contour | implicit `width_mm × height_mm` rectangle | new `Contour` on `ProductModule` — closed CCW segment loop (line/arc), exact `Decimal` |
| Region | `BAY` leaf of the split tree | region spec stays a `ParametricNode` BAY; non-rect region = contour interior offset (v1: single region/module) |
| Member | role + computed rect placement | member per contour edge: length = edge length, end cuts = corner_interior/2; arc members flagged `bending` |
| Path | none | `LinePath`/`ArcPath` inside the contour kernel; member generatrix derived from the edge |
| Connection | `CouplingDef` (linear chain) | stays linear in v3.0; typed kinds (`T`, `corner`, `stacked`) extend the same model later |
| Filling | `GlassPiece`/`PanelPiece` w×h | `GlassPiece` gains `polygon` (bbox stays width/height); panels likewise later |
| Opening | `BayOpeningType` enum | unchanged enum on BAY regions; region validity checked geometrically |
| HardwareSet | `hardware_set_sku` + kit rules | unchanged |
| Constraint | none | deferred: width/height/vertex constraints arrive with the contour editor |

## 2. Contour representation

```python
class Contour(EngineModel):
    """Closed CCW loop in module-local mm. vertices[i] → vertices[i+1] is
    edge i (the last edge closes to vertices[0]). `bulges[i]` is the
    signed sagitta of edge i: 0/None = straight line, nonzero = circular
    arc bulging toward the LEFT of the directed edge."""
    vertices: list[PointMm]      # ≥3, exact Decimal
    bulges: list[Decimal | None] # len == len(vertices)
```

- Validation: ≥3 vertices, non-self-intersecting, normalized CCW
  (positive signed area), no zero-length edges, arc sagitta < half-chord.
- Factory helpers: `Contour.rect(w,h)`, `Contour.trapezoid(w,h,offset_l,offset_r)`,
  `Contour.arch_top(w,h,rise)` — editor/AI never hand-builds vertex lists.
- `interior_offset(face_width_mm)` → fill polygon (line edges exact; arc
  edges offset radius − face_width toward the center).

## 3. Member model (v3.0 scope)

Each contour edge → one `ProfileCut` (role FRAME):

- `length_mm` = chord length (line) or arc length (arc).
- `angle_left`/`angle_right` = half the interior angle at each adjacent
  vertex (a rectangle degenerates to the proven 45° welded miters).
- Arc members carry `sagitta_mm` — non-null marks them `curved`: they
  emit a `bending_required` manufacturing warning rather than fake a
  bending rule (catalogs may declare bending authority later).
- Members keep `bay_id`/`leaf_id` prefixing and semantic-member traces
  (`edge:{index}` adds topology identity for traceability).

## 4. Regions and splits

- Non-rect contour modules evaluate exactly one region: the interior
  offset polygon. The module `tree` stays a single BAY leaf carrying
  `opening_type`, `glass_*`, `hardware_set_sku` — the region spec
  machinery is reused untouched.
- Splits on non-rect contours are rejected with
  `splits_unsupported_on_contour` (honest, per §10 of the mandate —
  geometrically valid operations only) until the region-graph work lands.
- Rect contours may use the normal split tree: a rect contour with a
  split tree evaluates through the classic path (tree wins when contour
  is a plain rectangle — keeps one geometry path for all existing data).

## 5. Geometry math (Decimal, deterministic)

- Interior angle at vertex i from adjacent edge directions; arc edges
  contribute their tangent at the vertex.
- Line–line offset edges intersect exactly; line–arc offsets resolve
  analytically (circle–line intersection, no float: `Decimal` sqrt via
  `trig`/exact helpers — reuses `dekopen_engine.trig` conventions).
- Self-intersection checks: segment–segment for lines; arc edges are
  chord-sampled at 1 mm for intersection testing (validation only —
  never for geometry output).
- Glass polygon: shoelace area → `area_m2`; weight via
  `derive_net_glass_thickness × 2.5 kg/m²/mm`; `polygon` vertices emitted
  on `GlassPiece` for downstream cutting/documents.

## 6. What stays linear — for now

`CouplingDef` remains a linear chain connection. T-connections, corner
posts, stacked rows and door+transom+sidelight compositions extend the
same `CoupledAssembly` by adding `Connection` kinds after the contour
vertical slices prove the member model — per mandate: "do not
prematurely build an unrestricted graph editor".

## 7. Migration / compatibility

- `ProductModule.contour` is optional; every stored product parses and
  evaluates identically (field absent → rectangle path).
- A rect `Contour` produced by a starter serializes the same v2 JSON
  shape — sealed documents keep exact hashes.
- Legacy editing: the editor adapts rect modules into contour editing
  only when the user asks (shape convert command); classic products open
  unchanged.
- `GlassPiece.polygon` / `ProfileCut.sagitta_mm` are optional — old
  sealed BOMs deserialize without them.
