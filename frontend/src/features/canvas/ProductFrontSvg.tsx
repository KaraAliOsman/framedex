import { useEffect, useState, type KeyboardEvent } from "react";

import type { ProductIssue } from "../../api/generated/models";
import { t } from "../../i18n/es-CL";
import type { IntentNode } from "./intentEditing";
import { memberSurface, type MemberSurface } from "./materials";
import type { MemberGeometry } from "./members";
import type { ProductJson } from "./productEditing";

/** Front elevation of the compositional product as a real fenestration
 * drawing: frame/sash/mullion/bead/threshold members at their catalog face
 * widths, glass and panel infills, handle levers, signature dimension chains
 * with extension lines and ticks. The engine stays the authority — this view
 * only renders and dispatches typed edits. */

type SeverityMap = Map<string, "error" | "warning">;

function severityByModule(issues: ProductIssue[]): SeverityMap {
  const map: SeverityMap = new Map();
  for (const issue of issues) {
    const target = issue.target;
    if (!target.startsWith("module:")) continue;
    const id = target.slice("module:".length);
    const current = map.get(id);
    if (current !== "error") map.set(id, issue.severity);
  }
  return map;
}

/** Click-to-edit dimension rendered on the canvas: idle text, input on click. */
function SvgDim({
  x,
  y,
  value,
  label,
  active,
  disabled,
  onCommit,
}: {
  x: number;
  y: number;
  value: string;
  label: string;
  active?: boolean;
  disabled: boolean;
  onCommit(normalized: string): void;
}): JSX.Element {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(value);
  useEffect(() => {
    if (!editing) setDraft(value);
  }, [value, editing]);
  const fontSize = 34;
  if (!editing || disabled) {
    return (
      <text
        className={`canvas-dim${active ? " is-active" : ""}`}
        x={x}
        y={y}
        fontSize={fontSize}
        textAnchor="middle"
        dominantBaseline="central"
        role="button"
        aria-label={label}
        tabIndex={disabled ? -1 : 0}
        onClick={() => !disabled && setEditing(true)}
        onKeyDown={(event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            if (!disabled) setEditing(true);
          }
        }}
      >
        {value}
      </text>
    );
  }
  return (
    <foreignObject x={x - 70} y={y - fontSize} width={140} height={fontSize + 26}>
      <input
        className="canvas-dim-input"
        aria-label={label}
        autoFocus
        inputMode="decimal"
        value={draft}
        onChange={(event) => setDraft(event.target.value)}
        onFocus={(event) => event.target.select()}
        onBlur={() => {
          const normalized = normalizeDimension(draft);
          if (normalized !== null && normalized !== value) onCommit(normalized);
          setEditing(false);
        }}
        onKeyDown={(event) => {
          if (event.key === "Enter") event.currentTarget.blur();
          if (event.key === "Escape") {
            setDraft(value);
            event.currentTarget.blur();
          }
        }}
      />
    </foreignObject>
  );
}

function normalizeDimension(candidate: string): string | null {
  const value = Number(candidate.trim().replace(",", ".").replace(/[°\s]/g, ""));
  if (!Number.isFinite(value) || value <= 0) return null;
  return value.toFixed(2);
}

/** Industry opening glyph: hinge side = triangle base, handle = apex. */
export function OpeningGlyph({
  opening,
  x,
  y,
  w,
  h,
}: {
  opening: string | null | undefined;
  x: number;
  y: number;
  w: number;
  h: number;
}): JSX.Element {
  const padX = w * 0.12;
  const padY = h * 0.12;
  const left = x + padX;
  const right = x + w - padX;
  const top = y + padY;
  const bottom = y + h - padY;
  const cx = x + w / 2;
  const cy = y + h / 2;
  const kind = opening ?? "FIXED";
  return (
    <g className={`opening-glyph opening-${kind.toLowerCase()}`} aria-hidden="true">
      {kind.includes("RIGHT") && (
        <polyline points={`${right},${top} ${left},${cy} ${right},${bottom}`} fill="none" />
      )}
      {kind.includes("LEFT") && (
        <polyline points={`${left},${top} ${right},${cy} ${left},${bottom}`} fill="none" />
      )}
      {(kind.startsWith("TILT") || kind === "AWNING") && (
        <polyline points={`${left},${bottom} ${cx},${top} ${right},${bottom}`} fill="none" />
      )}
      {kind === "SLIDING_2L" && (
        <>
          <line x1={cx} y1={top} x2={cx} y2={bottom} />
          <path
            d={`M${x + w * 0.2} ${cy} H${x + w * 0.42} M${x + w * 0.38} ${cy - h * 0.05} L${x + w * 0.44} ${cy}`}
            fill="none"
          />
          <path
            d={`M${x + w * 0.8} ${cy} H${x + w * 0.58} M${x + w * 0.62} ${cy + h * 0.05} L${x + w * 0.56} ${cy}`}
            fill="none"
          />
        </>
      )}
      {kind === "DOOR_ENTRY" && <line x1={left} y1={top} x2={right} y2={bottom} opacity={0.35} />}
      {kind === "FIXED" && <line x1={left} y1={top} x2={right} y2={bottom} opacity={0.18} />}
    </g>
  );
}

type Region = { x: number; y: number; w: number; h: number };

/** Rectangular member drawn as a filled ring segment: outer rect minus inner
 * rect (evenodd) — frame, sash, mullion, threshold and coupler all share it. */
function Member({
  x,
  y,
  w,
  h,
  surface,
  className,
}: {
  x: number;
  y: number;
  w: number;
  h: number;
  surface: MemberSurface;
  className: string;
}): JSX.Element {
  return (
    <rect
      className={`member ${className}`}
      x={x}
      y={y}
      width={w}
      height={h}
      fill={surface.fill}
      stroke={surface.edge}
      strokeWidth={2.5}
    />
  );
}

/** Handle lever on the sash's handle edge (≈55% up, EN convention). */
function HandleLever({
  x,
  y,
  side,
}: {
  x: number;
  y: number;
  side: "left" | "right";
}): JSX.Element {
  const dir = side === "left" ? 1 : -1;
  return (
    <g className="handle-lever" aria-hidden="true">
      <line x1={x} y1={y - 10} x2={x} y2={y + 16} strokeWidth={5} strokeLinecap="round" />
      <line x1={x} y1={y} x2={x + dir * 18} y2={y} strokeWidth={5} strokeLinecap="round" />
    </g>
  );
}

/** A leaf bay: sash ring (when operable), glazing bead sightline, glass or
 * panel infill, opening glyph and handle lever. */
function Bay({
  node,
  region,
  members,
}: {
  node: IntentNode;
  region: Region;
  members: MemberGeometry;
}): JSX.Element {
  const opening = node.opening_type ?? "FIXED";
  const bead = members.beadFor(node.glass_thickness_mm ?? null);
  const sashSurface = memberSurface(members.sash.material);

  // Two-track slider: two sash leaves with their meeting-stile interlock —
  // the rear leaf draws first, the front leaf covers the overlap.
  if (opening === "SLIDING_2L") {
    const interlock = members.sash.faceWidthMm;
    const leafW = (region.w + interlock) / 2;
    const leaves: Region[] = [
      { x: region.x, y: region.y, w: leafW, h: region.h },
      { x: region.x + region.w - leafW, y: region.y, w: leafW, h: region.h },
    ];
    return (
      <g className="module-bay module-bay--sliding">
        {leaves.map((leaf, index) => {
          const leafSashT = members.sash.faceWidthMm;
          const beadX = leaf.x + leafSashT;
          const beadY = leaf.y + leafSashT;
          const beadW = leaf.w - leafSashT * 2;
          const beadH = leaf.h - leafSashT * 2;
          return (
            <g
              key={`leaf-${index}`}
              className={`sliding-leaf sliding-leaf--${index === 0 ? "rear" : "front"}`}
            >
              <Member
                x={leaf.x}
                y={leaf.y}
                w={leaf.w}
                h={leaf.h}
                surface={sashSurface}
                className="member-sash"
              />
              <rect
                className="member-bead"
                x={beadX}
                y={beadY}
                width={Math.max(beadW, 0)}
                height={Math.max(beadH, 0)}
              />
              <rect
                className="module-glass"
                x={beadX + bead}
                y={beadY + bead}
                width={Math.max(beadW - bead * 2, 0)}
                height={Math.max(beadH - bead * 2, 0)}
              />
            </g>
          );
        })}
        {region.w > 60 && region.h > 60 && (
          <OpeningGlyph
            opening={node.opening_type}
            x={region.x}
            y={region.y}
            w={region.w}
            h={region.h}
          />
        )}
      </g>
    );
  }

  const isDoor = opening === "DOOR_ENTRY";
  const operable = opening !== "FIXED";
  const reveal = 3;

  const thresholdH = isDoor ? (members.threshold?.faceWidthMm ?? 30) : 0;
  const sashArea: Region = operable
    ? {
        x: region.x + reveal,
        y: region.y + reveal,
        w: region.w - reveal * 2,
        h: region.h - reveal * 2 - thresholdH,
      }
    : region;
  const sashT = members.sash.faceWidthMm;
  const glass: Region = operable
    ? {
        x: sashArea.x + sashT,
        y: sashArea.y + sashT,
        w: sashArea.w - sashT * 2,
        h: sashArea.h - sashT * 2,
      }
    : {
        x: region.x + bead,
        y: region.y + bead,
        w: region.w - bead * 2,
        h: region.h - bead * 2,
      };
  const pane: Region = operable
    ? { x: glass.x + bead, y: glass.y + bead, w: glass.w - bead * 2, h: glass.h - bead * 2 }
    : glass;
  const isPanel = Boolean(node.panel_article_sku);
  const handleSide = opening.includes("LEFT")
    ? "right"
    : opening.includes("RIGHT") || isDoor
      ? "left"
      : null;

  return (
    <g className="module-bay">
      {operable && (
        <>
          <Member
            x={sashArea.x}
            y={sashArea.y}
            w={sashArea.w}
            h={Math.max(sashArea.h, 0)}
            surface={sashSurface}
            className="member-sash"
          />
          {/* glazing beads: sightline ring inside the sash */}
          <rect
            className="member-bead"
            x={glass.x}
            y={glass.y}
            width={Math.max(glass.w, 0)}
            height={Math.max(glass.h, 0)}
          />
        </>
      )}
      {isPanel ? (
        <rect
          className="bay-panel"
          x={pane.x}
          y={pane.y}
          width={Math.max(pane.w, 0)}
          height={Math.max(pane.h, 0)}
        />
      ) : (
        <g>
          <rect
            className="module-glass"
            x={pane.x}
            y={pane.y}
            width={Math.max(pane.w, 0)}
            height={Math.max(pane.h, 0)}
          />
          {pane.w > 30 && pane.h > 30 && (
            <line
              className="glass-sheen"
              x1={pane.x + pane.w * 0.18}
              y1={pane.y + pane.h * 0.82}
              x2={pane.x + pane.w * 0.82}
              y2={pane.y + pane.h * 0.18}
            />
          )}
        </g>
      )}
      {isDoor && thresholdH > 0 && (
        <Member
          x={region.x}
          y={region.y + region.h - thresholdH}
          w={region.w}
          h={thresholdH}
          surface={memberSurface(members.threshold?.material ?? members.frame.material)}
          className="member-threshold"
        />
      )}
      {pane.w > 60 && pane.h > 60 && (
        <OpeningGlyph opening={node.opening_type} x={pane.x} y={pane.y} w={pane.w} h={pane.h} />
      )}
      {handleSide && operable && (
        <HandleLever
          x={
            handleSide === "right"
              ? sashArea.x + sashArea.w - sashT * 0.55
              : sashArea.x + sashT * 0.55
          }
          y={sashArea.y + sashArea.h * 0.55}
          side={handleSide}
        />
      )}
    </g>
  );
}

/** Render a module's parametric tree inside a region: splits become mullion
 * members at their catalog face width, bays render the full member hierarchy. */
function ModuleTree({
  node,
  region,
  localOrigin,
  members,
}: {
  node: IntentNode;
  region: Region;
  /** Sheet-space origin the node's split_offset_mm measures from — engine
   * parity: (0,0) = module outer edge for the top node, the node's own rect
   * origin for children. */
  localOrigin: { x: number; y: number };
  members: MemberGeometry;
}): JSX.Element {
  if (node.type === "ROOT" && node.children?.length === 1 && node.children[0]) {
    return (
      <ModuleTree
        node={node.children[0]}
        region={region}
        localOrigin={localOrigin}
        members={members}
      />
    );
  }
  if ((node.type === "SPLIT_V" || node.type === "SPLIT_H") && node.children?.length === 2) {
    const [first, second] = node.children;
    const vertical = node.type === "SPLIT_V";
    const mullion = vertical ? members.mullionV : members.mullionH;
    const barW = mullion?.faceWidthMm ?? Math.max(Math.min(region.w, region.h) * 0.05, 20);
    const lo = vertical ? region.x : region.y;
    const extent = vertical ? region.w : region.h;
    const offset = Number(node.split_offset_mm);
    // Engine parity (geometry._walk_node): the mullion centerline sits at
    // local-origin + split_offset_mm. The top node's origin is the module's
    // outer edge; each child's origin is its own rect's origin. Clamped into
    // the region for display only — the engine flags out-of-range offsets.
    const desired = (vertical ? localOrigin.x : localOrigin.y) + offset;
    const axis =
      Number.isFinite(offset) && offset > 0
        ? Math.min(Math.max(desired, lo + barW / 2), lo + extent - barW / 2)
        : lo + extent / 2;
    const firstRegion: Region = vertical
      ? { x: region.x, y: region.y, w: axis - barW / 2 - region.x, h: region.h }
      : { x: region.x, y: region.y, w: region.w, h: axis - barW / 2 - region.y };
    const secondRegion: Region = vertical
      ? {
          x: axis + barW / 2,
          y: region.y,
          w: region.x + region.w - (axis + barW / 2),
          h: region.h,
        }
      : {
          x: region.x,
          y: axis + barW / 2,
          w: region.w,
          h: region.y + region.h - (axis + barW / 2),
        };
    const bar: Region =
      node.type === "SPLIT_V"
        ? { x: axis - barW / 2, y: region.y, w: barW, h: region.h }
        : { x: region.x, y: axis - barW / 2, w: region.w, h: barW };
    return (
      <>
        <ModuleTree
          node={first!}
          region={firstRegion}
          localOrigin={{ x: firstRegion.x, y: firstRegion.y }}
          members={members}
        />
        <Member
          x={bar.x}
          y={bar.y}
          w={Math.max(bar.w, 0)}
          h={Math.max(bar.h, 0)}
          surface={memberSurface(mullion?.material ?? members.frame.material)}
          className="member-mullion"
        />
        <ModuleTree
          node={second!}
          region={secondRegion}
          localOrigin={{ x: secondRegion.x, y: secondRegion.y }}
          members={members}
        />
      </>
    );
  }
  return <Bay node={node} region={region} members={members} />;
}

const TOP_GUTTER = 150;
const SIDE_GUTTER = 130;
const BOTTOM_GUTTER = 120;
const LEFT_GUTTER = 170;

/** Architectural dimension run: extension lines from the measured edge out
 * to the dim line (overshooting it slightly), diagonal ticks at each mark,
 * mono labels placed by the caller between them. */
function DimRun({
  marks,
  edge,
  at,
  vertical,
}: {
  /** axis positions (x for horizontal runs, y for vertical) of each measured edge */
  marks: number[];
  /** cross-axis coordinate where the measured edge sits (extensions start here) */
  edge: number;
  /** cross-axis coordinate of the dim line itself */
  at: number;
  vertical: boolean;
}): JSX.Element {
  const first = Math.min(...marks);
  const last = Math.max(...marks);
  const direction = at > edge ? 1 : -1;
  const overshoot = at + direction * 14;
  return (
    <g className="dim-run" aria-hidden="true">
      {marks.map((mark, index) =>
        vertical ? (
          <line
            key={`ext-${index}`}
            className="dim-extension"
            x1={edge}
            y1={mark}
            x2={overshoot}
            y2={mark}
          />
        ) : (
          <line
            key={`ext-${index}`}
            className="dim-extension"
            x1={mark}
            y1={edge}
            x2={mark}
            y2={overshoot}
          />
        ),
      )}
      {vertical ? (
        <line className="dim-line" x1={at} y1={first} x2={at} y2={last} />
      ) : (
        <line className="dim-line" x1={first} y1={at} x2={last} y2={at} />
      )}
      {marks.map((mark, index) =>
        vertical ? (
          <line
            key={`tick-${index}`}
            className="dim-tick"
            x1={at - 8}
            y1={mark + 8}
            x2={at + 8}
            y2={mark - 8}
          />
        ) : (
          <line
            key={`tick-${index}`}
            className="dim-tick"
            x1={mark - 8}
            y1={at + 8}
            x2={mark + 8}
            y2={at - 8}
          />
        ),
      )}
    </g>
  );
}

function AddHandle({
  x,
  y,
  label,
  disabled,
  onAdd,
}: {
  x: number;
  y: number;
  label: string;
  disabled: boolean;
  onAdd(): void;
}): JSX.Element {
  return (
    <g
      className="add-handle"
      role="button"
      aria-label={label}
      tabIndex={disabled ? -1 : 0}
      onClick={() => !disabled && onAdd()}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          if (!disabled) onAdd();
        }
      }}
    >
      <circle cx={x} cy={y} r={34} />
      <path d={`M${x - 14} ${y} H${x + 14} M${x} ${y - 14} V${y + 14}`} />
    </g>
  );
}

export interface FrontModuleRect {
  module: ProductJson["assembly"]["modules"][number];
  x: number;
  w: number;
}

export interface FrontLayout {
  rects: FrontModuleRect[];
  totalW: number;
  height: number;
}

/** Module frame rectangles: frames abut and the drawn width stays the
 * domain's nominal Σ-module width (couplers overlay their joint instead of
 * widening the elevation). */
export function frontLayout(product: ProductJson): FrontLayout {
  const { modules } = product.assembly;
  let cursor = 0;
  const rects = modules.map((module) => {
    const width = Number(module.width_mm);
    const rect = { module, x: cursor, w: width };
    cursor += width;
    return rect;
  });
  return {
    rects,
    totalW: cursor,
    height: Math.max(...modules.map((module) => Number(module.height_mm))),
  };
}

/** The drawable extent of the front elevation including gutters and chains. */
export function frontBounds(product: ProductJson) {
  const { totalW, height } = frontLayout(product);
  return {
    x: -LEFT_GUTTER,
    y: -TOP_GUTTER,
    w: totalW + LEFT_GUTTER + SIDE_GUTTER,
    h: height + TOP_GUTTER + BOTTOM_GUTTER,
  };
}

/** Sheet-space box of a module's frame — the Shift+2 / zoom-to-selection target. */
export function frontModuleBox(product: ProductJson, moduleId: string | null) {
  if (!moduleId) return null;
  const rect = frontLayout(product).rects.find((item) => item.module.id === moduleId);
  if (!rect) return null;
  const height = frontLayout(product).height;
  return { x: rect.x - 30, y: -60, w: rect.w + 60, h: height + 150 };
}

export function ProductFrontContent({
  product,
  members,
  selectedId,
  issues,
  disabled,
  preview = false,
  onSelectModule,
  onAddUnit,
  onCommitModuleWidth,
  onCommitTotalWidth,
  onCommitHeight,
}: {
  product: ProductJson;
  members: MemberGeometry;
  selectedId: string | null;
  issues: ProductIssue[];
  disabled: boolean;
  /** Thumbnail mode: draws the members but strips every interactive
   * affordance (roles, tab stops, handlers) so it can live inside a
   * single outer button. */
  preview?: boolean;
  onSelectModule(moduleId: string): void;
  onAddUnit(side: "left" | "right"): void;
  onCommitModuleWidth(moduleId: string, widthMm: string): void;
  onCommitTotalWidth(totalMm: string): void;
  onCommitHeight(heightMm: string): void;
}): JSX.Element {
  const { couplings } = product.assembly;
  const frameT = members.frame.faceWidthMm;
  const frameSurface = memberSurface(members.frame.material);
  const { rects, totalW, height } = frontLayout(product);
  const issueMap = severityByModule(issues);
  const midY = height / 2;

  return (
    <g className="product-front-svg" data-testid="product-front">
      {/* overall width chain */}
      <DimRun marks={[0, totalW]} edge={0} at={-70} vertical={false} />
      <SvgDim
        x={totalW / 2}
        y={-70}
        value={totalW.toFixed(2)}
        label={t("assembly.totalWidth")}
        disabled={disabled}
        onCommit={onCommitTotalWidth}
      />
      {/* height chain */}
      <DimRun marks={[0, height]} edge={0} at={-110} vertical={true} />
      <g transform={`rotate(-90 ${-110} ${midY})`}>
        <SvgDim
          x={-110}
          y={midY}
          value={height.toFixed(2)}
          label={t("assembly.height")}
          disabled={disabled}
          onCommit={onCommitHeight}
        />
      </g>
      {/* per-module width chain */}
      <DimRun
        marks={rects.flatMap(({ x, w }) => [x, x + w])}
        edge={height}
        at={height + 80}
        vertical={false}
      />
      {rects.map(({ module, x, w }) => (
        <SvgDim
          key={`dim-${module.id}`}
          x={x + w / 2}
          y={height + 80}
          value={w.toFixed(2)}
          label={`${t("assembly.module")} ${module.id} ${t("assembly.width")}`}
          active={module.id === selectedId}
          disabled={disabled}
          onCommit={(value) => onCommitModuleWidth(module.id, value)}
        />
      ))}
      <AddHandle
        x={-70}
        y={midY}
        label={t("assembly.addUnitLeft")}
        disabled={disabled}
        onAdd={() => onAddUnit("left")}
      />
      <AddHandle
        x={totalW + 70}
        y={midY}
        label={t("assembly.addUnitRight")}
        disabled={disabled}
        onAdd={() => onAddUnit("right")}
      />
      {rects.map(({ module, x, w }) => (
        <g
          key={module.id}
          className={`front-module${module.id === selectedId ? " is-selected" : ""}${issueMap.get(module.id) === "error" ? " has-error" : issueMap.get(module.id) === "warning" ? " has-warning" : ""}`}
          {...(preview
            ? { role: "presentation", "aria-hidden": true }
            : {
                role: "button",
                "aria-label": `${t("assembly.module")} ${module.id}`,
                "aria-pressed": module.id === selectedId,
                tabIndex: disabled ? -1 : 0,
                onClick: () => onSelectModule(module.id),
                onKeyDown: (event: KeyboardEvent) => {
                  if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    onSelectModule(module.id);
                  }
                },
              })}
        >
          <Member x={x} y={0} w={w} h={height} surface={frameSurface} className="member-frame" />
          <rect
            className="module-opening"
            x={x + frameT}
            y={frameT}
            width={Math.max(w - frameT * 2, 0)}
            height={Math.max(height - frameT * 2, 0)}
          />
          <ModuleTree
            node={module.tree}
            region={{ x: x + frameT, y: frameT, w: w - frameT * 2, h: height - frameT * 2 }}
            localOrigin={{ x, y: 0 }}
            members={members}
          />
        </g>
      ))}
      {couplings.map((coupling, index) => {
        const prev = rects[index];
        if (!prev) return null;
        const width = members.couplerFor(coupling.coupler_profile_sku)?.faceWidthMm ?? 60;
        const x = prev.x + prev.w - width / 2;
        return (
          <Member
            key={coupling.id}
            x={x}
            y={0}
            w={width}
            h={height}
            surface={memberSurface(
              members.couplerFor(coupling.coupler_profile_sku)?.material ?? members.frame.material,
            )}
            className="member-coupler"
          />
        );
      })}
    </g>
  );
}

/** Standalone front elevation with its own viewBox — the sheet viewer
 * (CanvasViewport) renders `ProductFrontContent` inside its own transform
 * instead; this wrapper stays for any consumer that just wants an SVG. */
export function ProductFrontSvg(props: Parameters<typeof ProductFrontContent>[0]): JSX.Element {
  const bounds = frontBounds(props.product);
  return (
    <svg
      className="product-front-svg"
      viewBox={`${bounds.x} ${bounds.y} ${bounds.w} ${bounds.h}`}
      role="img"
      aria-label={t("assembly.frontView")}
    >
      <ProductFrontContent {...props} />
    </svg>
  );
}
