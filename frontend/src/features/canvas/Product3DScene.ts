import type { PlanGeometry, PlanModule } from "../../api/generated/models";
import type { ProductJson, ProductModuleJson } from "./productEditing";
import { modulePrimaryBay, resolveStacks } from "./productEditing";
import type { IntentNode } from "./intentEditing";
import { resolvedSlidingLayout } from "./intentEditing";
import { insetContourPoints } from "./contourGeometry";
import { frontLayout } from "./ProductFrontSvg";
import type { MemberGeometry } from "./members";

/** Pure 3D scene builder — the §16 view derives every solid from the SAME
 * product model the 2D elevation renders (front layout, bay tree, catalog
 * member geometry, engine plan corners). There is no separate 3D data
 * model: if a fact isn't declared (section depth, plan depth), the solid
 * falls back to a neutral convention, never to a fabricated declaration. */

export type Pt2 = [number, number];
export type Vec3 = [number, number, number];

export type SolidKind =
  "frame" | "sash" | "mullion" | "glass" | "panel" | "coupler" | "support" | "fitting";

export interface BoxSolid {
  kind: "box";
  owner: string;
  surface: SolidKind;
  material: string;
  center: Vec3;
  size: Vec3;
}

/** Member ring / pane extruded along the module's depth axis from a
 * module-local outline (x right, y up — the contour space). The extrusion
 * spans z0..z0+depth so glazing can sit inside the profile depth. */
export interface ShapeSolid {
  kind: "shape";
  owner: string;
  surface: SolidKind;
  material: string;
  outline: Pt2[];
  holes: Pt2[][];
  z0: number;
  depth: number;
}

/** Coupler wedge in world space: a plan polygon (x,z) extruded vertically. */
export interface PrismSolid {
  kind: "prism";
  owner: string;
  surface: SolidKind;
  material: string;
  outline: Pt2[];
  y0: number;
  y1: number;
}

export type Solid3D = BoxSolid | ShapeSolid | PrismSolid;

export interface ModuleScene {
  moduleId: string;
  /** World placement of the module-local frame (x right, y up, z into the
   * wall): from the engine plan corners — start corner → position, heading
   * → rotation about +Y. */
  position: Vec3;
  rotationY: number;
  /** Module depth — stack coupler bars are emitted in this local frame. */
  depth: number;
  solids: Solid3D[];
}

export interface Scene3D {
  modules: ModuleScene[];
  couplers: Solid3D[];
  /** Camera-fit volume over the whole scene. */
  center: Vec3;
  radius: number;
}

/** Neutral drawing depth when no authority declares one — the plan carries
 * the system's depth_mm whenever an evaluation exists; the fallback only
 * applies offline. */
const FALLBACK_DEPTH_MM = 60;
const GLASS_DEFAULT_MM = 20;
const SUPPORT_CHANNEL_MM = 14;
const FITTING_BLOCK_MM = 90;

type Region = { x: number; y: number; w: number; h: number };
type NodeRegion = { node: IntentNode; region: Region };

function box(
  owner: string,
  surface: SolidKind,
  material: string,
  x: number,
  y: number,
  z: number,
  w: number,
  h: number,
  d: number,
): BoxSolid {
  return {
    kind: "box",
    owner,
    surface,
    material,
    center: [x + w / 2, y + h / 2, z + d / 2],
    size: [w, h, d],
  };
}

/** Four-member ring inside a region (long sides full span, caps between). */
function memberBarRing(
  solids: Solid3D[],
  owner: string,
  surface: SolidKind,
  material: string,
  region: Region,
  barW: number,
  depth: number,
  z0: number,
): void {
  const w = Math.min(barW, region.w / 2);
  const h = Math.min(barW, region.h / 2);
  solids.push(
    box(owner, surface, material, region.x, region.y, z0, w, region.h, depth),
    box(owner, surface, material, region.x + region.w - w, region.y, z0, w, region.h, depth),
    box(owner, surface, material, region.x + w, region.y, z0, region.w - 2 * w, h, depth),
    box(
      owner,
      surface,
      material,
      region.x + w,
      region.y + region.h - h,
      z0,
      region.w - 2 * w,
      h,
      depth,
    ),
  );
}

/** Split walk that emits both divider bars and leaf bays — the same layout
 * math `ModuleTree`/`bayRegions` render in 2D. */
function walkNode(
  node: IntentNode,
  region: Region,
  origin: { x: number; y: number },
  members: MemberGeometry,
  out: { bars: { node: IntentNode; region: Region; vertical: boolean }[]; leaves: NodeRegion[] },
): void {
  if (node.type === "ROOT" && node.children?.length === 1 && node.children[0]) {
    walkNode(node.children[0], region, origin, members, out);
    return;
  }
  if ((node.type === "SPLIT_V" || node.type === "SPLIT_H") && node.children?.length === 2) {
    const [first, second] = node.children;
    const vertical = node.type === "SPLIT_V";
    const mullion = vertical ? members.mullionV : members.mullionH;
    const barW = mullion?.faceWidthMm ?? Math.max(Math.min(region.w, region.h) * 0.05, 20);
    const lo = vertical ? region.x : region.y;
    const extent = vertical ? region.w : region.h;
    const offset = Number(node.split_offset_mm);
    const desired = (vertical ? origin.x : origin.y) + offset;
    const axis =
      Number.isFinite(offset) && offset > 0
        ? Math.min(Math.max(desired, lo + barW / 2), lo + extent - barW / 2)
        : lo + extent / 2;
    const firstRegion: Region = vertical
      ? { x: region.x, y: region.y, w: axis - barW / 2 - region.x, h: region.h }
      : { x: region.x, y: region.y, w: region.w, h: axis - barW / 2 - region.y };
    const secondRegion: Region = vertical
      ? { x: axis + barW / 2, y: region.y, w: region.x + region.w - (axis + barW / 2), h: region.h }
      : {
          x: region.x,
          y: axis + barW / 2,
          w: region.w,
          h: region.y + region.h - (axis + barW / 2),
        };
    walkNode(first!, firstRegion, { x: firstRegion.x, y: firstRegion.y }, members, out);
    walkNode(second!, secondRegion, { x: secondRegion.x, y: secondRegion.y }, members, out);
    out.bars.push({
      node,
      vertical,
      region: vertical
        ? { x: axis - barW / 2, y: region.y, w: barW, h: region.h }
        : { x: region.x, y: axis - barW / 2, w: region.w, h: barW },
    });
    return;
  }
  out.leaves.push({ node, region });
}

/** Module world placement from the engine plan corners — corners are
 * [start, end, back_end, back_start] in plan (x right, y up). World maps
 * (px, py) → (px, −py): the front heading becomes +X and the back edge
 * runs into +Z. rotationY = θ puts local +X along the heading. */
function planTransform(
  planModule: PlanModule | undefined,
  rect: { x: number; sill: number },
  fallbackDepth: number,
): { position: Vec3; rotationY: number; depth: number; fromPlan: boolean } {
  if (planModule && planModule.corners.length >= 4) {
    const [start, end, , backStart] = planModule.corners;
    if (start && end && backStart) {
      const theta = Math.atan2(
        Number(end.y_mm) - Number(start.y_mm),
        Number(end.x_mm) - Number(start.x_mm),
      );
      const depth = Math.hypot(
        Number(backStart.x_mm) - Number(start.x_mm),
        Number(backStart.y_mm) - Number(start.y_mm),
      );
      return {
        position: [Number(start.x_mm), rect.sill, -Number(start.y_mm)],
        rotationY: theta,
        depth: Number.isFinite(depth) && depth > 0 ? depth : fallbackDepth,
        fromPlan: true,
      };
    }
  }
  return {
    position: [rect.x, rect.sill, 0],
    rotationY: 0,
    depth: fallbackDepth,
    fromPlan: false,
  };
}

/** Leaf bay solids: sliding panes ride their declared tracks at stepped
 * depths, operable leaves get a sash ring + pane, fixed leaves a pane,
 * panels an opaque slab. */
function leafSolids(
  solids: Solid3D[],
  module: ProductModuleJson,
  bay: IntentNode,
  region: Region,
  members: MemberGeometry,
  depth: number,
): void {
  const owner = `${module.id}/${bay.id}`;
  const bead = members.beadFor(bay.glass_thickness_mm ?? null);
  const sliding = resolvedSlidingLayout(bay);
  const operable = sliding !== null || (bay.opening_type != null && bay.opening_type !== "FIXED");
  const declaredT = Number(bay.glass_thickness_mm);
  const glassT = Math.max(
    Number.isFinite(declaredT) && declaredT > 0 ? declaredT : GLASS_DEFAULT_MM,
    4,
  );
  const glassZ = Math.max((depth - glassT) / 2, 0);

  if (sliding && sliding.panels.length > 0) {
    // Slot geometry mirrors the front view: each slot is `pitch` wide, a
    // moving leaf covers its slot plus the meeting-stile interlock and is
    // clamped inside the bay; fixed panels glaze their slot directly.
    const pitch = region.w / sliding.panels.length;
    const interlock = members.sash.faceWidthMm;
    const leafW = pitch + interlock;
    const trackStep = Math.min(24, Math.max(depth * 0.18, 10));
    const sashD = Math.min(24, depth * 0.4);
    sliding.panels.forEach((panel, index) => {
      // FIXED panels declare track:null — they sit on the outer glazing
      // plane (front-most slot), not on a moving rail.
      const track =
        panel.track ??
        (panel.kind === "FIXED" ? sliding.tracks - 1 : index % Math.max(sliding.tracks, 1));
      const z0 = Math.min(glassZ + (sliding.tracks - 1 - track) * trackStep, depth - glassT);
      const slotX = region.x + pitch * index;
      if (panel.kind === "FIXED") {
        // Fixed slots glaze directly — no sash, same as the front view.
        solids.push(
          box(
            owner,
            "glass",
            "GLASS",
            slotX + bead,
            region.y + bead,
            z0,
            Math.max(pitch - 2 * bead, 1),
            Math.max(region.h - 2 * bead, 1),
            glassT,
          ),
        );
        return;
      }
      const leafX = Math.min(
        Math.max(slotX - interlock / 2, region.x),
        region.x + region.w - leafW,
      );
      const paneRegion: Region = { x: leafX, y: region.y, w: leafW, h: region.h };
      const sashW = Math.min(members.sash.faceWidthMm, leafW / 3, region.h / 3);
      memberBarRing(
        solids,
        owner,
        "sash",
        members.sash.material,
        paneRegion,
        sashW,
        sashD,
        Math.max(z0 - sashD, 0),
      );
      solids.push(
        box(
          owner,
          "glass",
          "GLASS",
          paneRegion.x + sashW,
          paneRegion.y + sashW,
          z0,
          Math.max(leafW - 2 * sashW, 1),
          Math.max(paneRegion.h - 2 * sashW, 1),
          glassT,
        ),
      );
    });
    return;
  }

  if (bay.panel_article_sku && !operable) {
    solids.push(
      box(
        owner,
        "panel",
        members.frame.material,
        region.x + bead,
        region.y + bead,
        glassZ,
        Math.max(region.w - 2 * bead, 1),
        Math.max(region.h - 2 * bead, 1),
        glassT,
      ),
    );
    return;
  }

  if (operable) {
    const sashW = Math.min(members.sash.faceWidthMm, region.w / 3, region.h / 3);
    const sashD = depth * 0.45;
    memberBarRing(
      solids,
      owner,
      "sash",
      members.sash.material,
      region,
      sashW,
      sashD,
      depth - sashD,
    );
    // An operable bay's infill sits inside its sash — an opaque panel for
    // panel doors, glazing otherwise (the front view wraps both the same).
    solids.push(
      box(
        owner,
        bay.panel_article_sku ? "panel" : "glass",
        bay.panel_article_sku ? members.frame.material : "GLASS",
        region.x + sashW,
        region.y + sashW,
        glassZ,
        Math.max(region.w - 2 * sashW, 1),
        Math.max(region.h - 2 * sashW, 1),
        glassT,
      ),
    );
    return;
  }

  solids.push(
    box(
      owner,
      "glass",
      "GLASS",
      region.x + bead,
      region.y + bead,
      glassZ,
      Math.max(region.w - 2 * bead, 1),
      Math.max(region.h - 2 * bead, 1),
      glassT,
    ),
  );
}

/** Glass-only module: the pane IS the module. Supports map to their
 * declared edges; fittings carry no position authority, so they render at
 * conventional spots (patch corners, lock at handle height) purely as a
 * visualization cue — counts and SKUs stay exact. */
function framelessSolids(
  solids: Solid3D[],
  module: ProductModuleJson,
  w: number,
  h: number,
  depth: number,
): void {
  const spec = module.frameless;
  if (!spec) return;
  const owner = module.id;
  const reveal = 6;
  // The pane is the bay's declared glass — the primary bay carries the
  // selected thickness, falling back to the neutral default only when
  // nothing is declared.
  const declaredT = Number(modulePrimaryBay(module)?.glass_thickness_mm);
  const glassT = Math.max(
    Number.isFinite(declaredT) && declaredT > 0 ? declaredT : GLASS_DEFAULT_MM,
    4,
  );
  solids.push(
    box(
      owner,
      "glass",
      "GLASS",
      reveal,
      reveal,
      Math.max((depth - glassT) / 2, 0),
      Math.max(w - 2 * reveal, 1),
      Math.max(h - 2 * reveal, 1),
      glassT,
    ),
  );
  const edgeSpan = (edge: string): Region => {
    switch (edge) {
      case "left":
        return { x: 0, y: 0, w: SUPPORT_CHANNEL_MM, h };
      case "right":
        return { x: w - SUPPORT_CHANNEL_MM, y: 0, w: SUPPORT_CHANNEL_MM, h };
      case "top":
        return { x: 0, y: h - SUPPORT_CHANNEL_MM, w, h: SUPPORT_CHANNEL_MM };
      default:
        return { x: 0, y: 0, w, h: SUPPORT_CHANNEL_MM };
    }
  };
  for (const support of spec.supports) {
    const span = edgeSpan(support.edge);
    if (support.kind === "CHANNEL") {
      solids.push(
        box(
          owner,
          "support",
          "ALUMINIUM",
          span.x,
          span.y,
          depth * 0.35,
          span.w,
          span.h,
          SUPPORT_CHANNEL_MM * 2,
        ),
      );
      continue;
    }
    const qty = Math.max(Math.floor(support.qty) || 2, 1);
    const horizontal = support.edge === "top" || support.edge === "bottom";
    for (let i = 0; i < qty; i += 1) {
      const t = qty === 1 ? 0.5 : i / (qty - 1);
      const cx = horizontal ? span.x + t * Math.max(span.w - FITTING_BLOCK_MM, 0) : span.x;
      const cy = horizontal ? span.y : span.y + t * Math.max(span.h - FITTING_BLOCK_MM, 0);
      solids.push(
        box(
          owner,
          "support",
          "ALUMINIUM",
          cx,
          cy,
          depth * 0.35,
          horizontal ? FITTING_BLOCK_MM : span.w,
          horizontal ? span.h : FITTING_BLOCK_MM,
          SUPPORT_CHANNEL_MM * 2,
        ),
      );
    }
  }
  const size = FITTING_BLOCK_MM * 0.6;
  for (const fitting of spec.fittings) {
    if (fitting.kind === "PATCH_FITTING") {
      solids.push(
        box(owner, "fitting", "STEEL", 0, 0, depth * 0.3, size, size, SUPPORT_CHANNEL_MM * 2),
        box(
          owner,
          "fitting",
          "STEEL",
          w - size,
          0,
          depth * 0.3,
          size,
          size,
          SUPPORT_CHANNEL_MM * 2,
        ),
      );
    } else if (fitting.kind === "LOCK") {
      const lockY = Math.min(1000, h * 0.7);
      solids.push(
        box(owner, "fitting", "STEEL", 0, lockY, depth * 0.3, size, size, SUPPORT_CHANNEL_MM * 2),
      );
    } else {
      solids.push(
        box(
          owner,
          "fitting",
          "STEEL",
          w / 2 - size / 2,
          0,
          depth * 0.3,
          size,
          size,
          SUPPORT_CHANNEL_MM * 2,
        ),
      );
    }
  }
}

/** Build the full 3D scene from the product + catalog member geometry +
 * engine plan (optional). World space: x = plan.x, y = elevation up,
 * z = −plan.y (depth into the wall). */
export function buildScene3D(
  product: ProductJson,
  members: MemberGeometry,
  plan?: PlanGeometry | null,
): Scene3D {
  const { rects, joints, columns } = frontLayout(product);
  const frameT = members.frame.faceWidthMm;
  const fallbackDepth = Math.max(
    Number(members.frame.section?.depth_mm) || FALLBACK_DEPTH_MM,
    frameT,
  );
  const planById = new Map((plan?.modules ?? []).map((module) => [module.module_id, module]));
  const moduleById = new Map(product.assembly.modules.map((module) => [module.id, module]));
  const moduleScenes: ModuleScene[] = [];
  const worldPoints: Vec3[] = [];

  const stacks = resolveStacks(product);
  for (const rect of rects) {
    const module = rect.module;
    const w = Number(module.width_mm);
    const h = Number(module.height_mm);
    const { position, rotationY, depth, fromPlan } = planTransform(
      planById.get(module.id),
      rect,
      fallbackDepth,
    );
    // A stacked member shares its root's plan footprint; the elevation
    // centres it inside the column, so offset along the root heading by
    // the same width difference (negative when the member protrudes).
    if (fromPlan && stacks.stackRoot.has(module.id)) {
      const root = moduleById.get(stacks.stackRoot.get(module.id) as string);
      const delta = (Number(root?.width_mm ?? w) - w) / 2;
      if (delta !== 0) {
        position[0] += delta * Math.cos(rotationY);
        position[2] += -delta * Math.sin(rotationY);
      }
    }
    const solids: Solid3D[] = [];

    if (module.frameless) {
      framelessSolids(solids, module, w, h, depth);
    } else if (module.contour) {
      // Contour modules extrude the real outline; like the 2D front view
      // they render no bay tree — the glazing is the contoured opening
      // itself, so the pane can never overhang a sloped or arched edge.
      solids.push({
        kind: "shape",
        owner: module.id,
        surface: "frame",
        material: members.frame.material,
        outline: insetContourPoints(module.contour, 0).map((p) => [p.x, p.y] as Pt2),
        holes: [insetContourPoints(module.contour, frameT).map((p) => [p.x, p.y] as Pt2)],
        z0: 0,
        depth,
      });
      const primaryBay = modulePrimaryBay(module);
      const bead = members.beadFor(primaryBay?.glass_thickness_mm ?? null);
      const declaredT = Number(primaryBay?.glass_thickness_mm);
      const glassT = Math.max(
        Number.isFinite(declaredT) && declaredT > 0 ? declaredT : GLASS_DEFAULT_MM,
        4,
      );
      const glassOutline = insetContourPoints(module.contour, frameT + bead).map(
        (p) => [p.x, p.y] as Pt2,
      );
      if (glassOutline.length >= 3) {
        solids.push({
          kind: "shape",
          owner: primaryBay ? `${module.id}/${primaryBay.id}` : module.id,
          surface: "glass",
          material: "GLASS",
          outline: glassOutline,
          holes: [],
          z0: Math.max((depth - glassT) / 2, 0),
          depth: glassT,
        });
      }
    } else {
      memberBarRing(
        solids,
        module.id,
        "frame",
        members.frame.material,
        { x: 0, y: 0, w, h },
        frameT,
        depth,
        0,
      );

      const out = {
        bars: [] as { node: IntentNode; region: Region; vertical: boolean }[],
        leaves: [] as NodeRegion[],
      };
      // The bay tree lives inside the frame aperture; split offsets stay
      // absolute from the module's outer corner, as ModuleTree does in 2D.
      walkNode(
        module.tree,
        { x: frameT, y: frameT, w: w - frameT * 2, h: h - frameT * 2 },
        { x: 0, y: 0 },
        members,
        out,
      );
      for (const bar of out.bars) {
        const mullion = bar.vertical ? members.mullionV : members.mullionH;
        solids.push(
          box(
            module.id,
            "mullion",
            mullion?.material ?? members.frame.material,
            bar.region.x,
            bar.region.y,
            0,
            Math.max(bar.region.w, 0.5),
            Math.max(bar.region.h, 0.5),
            depth,
          ),
        );
      }
      for (const leaf of out.leaves) {
        leafSolids(solids, module, leaf.node, leaf.region, members, depth);
      }
    }

    moduleScenes.push({ moduleId: module.id, position, rotationY, depth, solids });

    const cos = Math.cos(rotationY);
    const sin = Math.sin(rotationY);
    const corners: Vec3[] = [
      [0, 0, 0],
      [w, 0, 0],
      [0, h, 0],
      [w, h, 0],
      [0, 0, depth],
      [w, h, depth],
    ];
    for (const [cx, cy, cz] of corners) {
      worldPoints.push([
        position[0] + cx * cos + cz * sin,
        position[1] + cy,
        position[2] - cx * sin + cz * cos,
      ]);
    }
  }

  // Couplers: INLINE wedges come from the plan's coupling polygons; stack
  // contacts become horizontal bars at the member's sill line. Coupler
  // pair endpoints use the declared `modules` binding when present, else
  // the positional chain order (same convention the engine resolves).
  const couplers: Solid3D[] = [];
  // Pairs resolve with the same explicit-or-positional convention the
  // layout uses: `coupling.modules`, else index i binds modules i and i+1.
  const pairByCoupling = new Map(stacks.pairs.map(({ coupling, pair }) => [coupling.id, pair]));
  // A joint's top matches the front view's seam: the min of the two bound
  // ROOT columns' tops, where a column top counts every stacked member — a
  // transom's sill + height raises the seam above the root's own height.
  const topByRoot = new Map(columns.map((column) => [column.rootId, column.top]));
  const couplingHeight = (couplingId: string | null): number => {
    const pair = couplingId === null ? undefined : pairByCoupling.get(couplingId);
    if (!pair) return 0;
    const tops = pair
      .map((id) => topByRoot.get(stacks.stackRoot.get(id) ?? id))
      .filter((top): top is number => typeof top === "number");
    return tops.length > 0 ? Math.min(...tops) : 0;
  };
  for (const polygon of plan?.couplings ?? []) {
    const coupling = product.assembly.couplings.find((item) => item.id === polygon.coupling_id);
    const height = couplingHeight(polygon.coupling_id);
    if (polygon.polygon.length < 3 || height <= 0) continue;
    couplers.push({
      kind: "prism",
      owner: polygon.coupling_id,
      surface: "coupler",
      material:
        members.couplerFor(coupling?.coupler_profile_sku ?? null)?.material ??
        members.frame.material,
      outline: polygon.polygon.map((p) => [Number(p.x_mm), -Number(p.y_mm)] as Pt2),
      y0: 0,
      y1: height,
    });
    for (const p of polygon.polygon) {
      const x = Number(p.x_mm);
      const z = -Number(p.y_mm);
      worldPoints.push([x, 0, z], [x, height, z]);
    }
  }
  // Stack couplers live inside the member's local frame: the bar centres
  // on the member's sill line and follows its column's plan heading.
  for (const joint of joints) {
    if (joint.kind !== "stack" || !joint.couplingId) continue;
    const coupling = product.assembly.couplings.find((item) => item.id === joint.couplingId);
    const pair = pairByCoupling.get(joint.couplingId);
    const memberId = pair?.find((id) =>
      pair.some((other) => other !== id && stacks.stackParent.get(id) === other),
    );
    const memberScene = memberId
      ? moduleScenes.find((scene) => scene.moduleId === memberId)
      : undefined;
    const memberModule = memberId ? moduleById.get(memberId) : undefined;
    const barW = members.couplerFor(coupling?.coupler_profile_sku ?? null)?.faceWidthMm ?? 30;
    const solid = box(
      joint.couplingId,
      "coupler",
      members.couplerFor(coupling?.coupler_profile_sku ?? null)?.material ?? members.frame.material,
      0,
      -barW / 2,
      0,
      memberModule ? Number(memberModule.width_mm) : joint.w,
      barW,
      memberScene?.depth ?? fallbackDepth,
    );
    if (memberScene) {
      memberScene.solids.push(solid);
    } else {
      solid.center[0] = joint.x + solid.size[0] / 2;
      solid.center[1] = joint.y - barW / 2 + solid.size[1] / 2;
      couplers.push(solid);
      worldPoints.push([joint.x, joint.y, 0], [joint.x + joint.w, joint.y, 0]);
    }
  }

  if (worldPoints.length === 0) {
    return { modules: moduleScenes, couplers, center: [0, 0, 0], radius: 1000 };
  }
  const min: Vec3 = [Infinity, Infinity, Infinity];
  const max: Vec3 = [-Infinity, -Infinity, -Infinity];
  for (const p of worldPoints) {
    for (let i = 0; i < 3; i += 1) {
      min[i] = Math.min(min[i]!, p[i]!);
      max[i] = Math.max(max[i]!, p[i]!);
    }
  }
  const center: Vec3 = [(min[0] + max[0]) / 2, (min[1] + max[1]) / 2, (min[2] + max[2]) / 2];
  const radius = Math.max(Math.hypot(max[0] - min[0], max[1] - min[1], max[2] - min[2]) / 2, 200);
  return { modules: moduleScenes, couplers, center, radius };
}
