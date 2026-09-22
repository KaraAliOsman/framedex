import { useEffect, useState } from "react";

import type { ProductIssue } from "../../api/generated/models";
import { t } from "../../i18n/es-CL";
import type { IntentNode } from "./intentEditing";
import type { ProductJson } from "./productEditing";

/** Front elevation of the compositional product: real module proportions,
 * opening glyphs, click-to-edit dimensions, and add/remove affordances.
 * The engine stays the authority — this view only renders and dispatches
 * typed edits. */

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
  unit,
  label,
  disabled,
  onCommit,
}: {
  x: number;
  y: number;
  value: string;
  unit: string;
  label: string;
  disabled: boolean;
  onCommit(normalized: string): void;
}): JSX.Element {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(value);
  useEffect(() => {
    if (!editing) setDraft(value);
  }, [value, editing]);
  const fontSize = 42;
  if (!editing || disabled) {
    return (
      <text
        className="canvas-dim"
        x={x}
        y={y}
        fontSize={fontSize}
        textAnchor="middle"
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
        {unit}
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
      {kind === "DOOR_ENTRY" && (
        <>
          <line x1={left} y1={top} x2={right} y2={bottom} opacity={0.35} />
          <line
            x1={x}
            y1={y + h - h * 0.05}
            x2={x + w}
            y2={y + h - h * 0.05}
            strokeWidth={h * 0.02}
          />
          <circle cx={x + w * 0.82} cy={cy} r={Math.max(w, h) * 0.018} />
        </>
      )}
      {kind === "FIXED" && <line x1={left} y1={top} x2={right} y2={bottom} opacity={0.18} />}
    </g>
  );
}

type Region = { x: number; y: number; w: number; h: number };

/** Render a module's parametric tree inside a region: bays get opening
 * glyphs, splits become divider bars. Nested splits divide their region at
 * `split_offset_mm` when present, else evenly. */
function ModuleTree({
  node,
  region,
  moduleWidth,
}: {
  node: IntentNode;
  region: Region;
  moduleWidth: number;
}): JSX.Element {
  if (node.type === "ROOT" && node.children?.length === 1 && node.children[0]) {
    return <ModuleTree node={node.children[0]} region={region} moduleWidth={moduleWidth} />;
  }
  if ((node.type === "SPLIT_V" || node.type === "SPLIT_H") && node.children?.length === 2) {
    const [first, second] = node.children;
    const split = node as IntentNode;
    let ratio = 0.5;
    const offset = Number(split.split_offset_mm);
    const basis = node.type === "SPLIT_V" ? moduleWidth : region.h;
    if (Number.isFinite(offset) && offset > 0) {
      ratio = Math.min(Math.max(offset / basis, 0.1), 0.9);
    }
    const divider = Math.max(Math.min(region.w, region.h) * 0.025, 10);
    const firstRegion: Region =
      node.type === "SPLIT_V"
        ? { x: region.x, y: region.y, w: region.w * ratio, h: region.h }
        : { x: region.x, y: region.y, w: region.w, h: region.h * ratio };
    const secondRegion: Region =
      node.type === "SPLIT_V"
        ? {
            x: region.x + region.w * ratio + divider,
            y: region.y,
            w: region.w * (1 - ratio) - divider,
            h: region.h,
          }
        : {
            x: region.x,
            y: region.y + region.h * ratio + divider,
            w: region.w,
            h: region.h * (1 - ratio) - divider,
          };
    const bar: Region =
      node.type === "SPLIT_V"
        ? { x: region.x + region.w * ratio, y: region.y, w: divider, h: region.h }
        : { x: region.x, y: region.y + region.h * ratio, w: region.w, h: divider };
    return (
      <>
        <rect className="module-divider" x={bar.x} y={bar.y} width={bar.w} height={bar.h} />
        <ModuleTree node={first!} region={firstRegion} moduleWidth={moduleWidth} />
        <ModuleTree node={second!} region={secondRegion} moduleWidth={moduleWidth} />
      </>
    );
  }
  return (
    <g className="module-bay">
      <rect
        className="module-glass"
        x={region.x}
        y={region.y}
        width={Math.max(region.w, 0)}
        height={Math.max(region.h, 0)}
      />
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

const FRAME = 40;
const TOP_GUTTER = 150;
const SIDE_GUTTER = 130;
const BOTTOM_GUTTER = 110;
const LEFT_GUTTER = 170;

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

export function ProductFrontSvg({
  product,
  selectedId,
  issues,
  disabled,
  onSelectModule,
  onAddUnit,
  onCommitModuleWidth,
  onCommitTotalWidth,
  onCommitHeight,
}: {
  product: ProductJson;
  selectedId: string | null;
  issues: ProductIssue[];
  disabled: boolean;
  onSelectModule(moduleId: string): void;
  onAddUnit(side: "left" | "right"): void;
  onCommitModuleWidth(moduleId: string, widthMm: string): void;
  onCommitTotalWidth(totalMm: string): void;
  onCommitHeight(heightMm: string): void;
}): JSX.Element {
  const { modules } = product.assembly;
  const totalW = modules.reduce((total, module) => total + Number(module.width_mm), 0);
  const height = Math.max(...modules.map((module) => Number(module.height_mm)));
  const issueMap = severityByModule(issues);
  const selectedModule = modules.find((module) => module.id === selectedId);
  const midY = height / 2;
  let cursor = 0;
  const rects = modules.map((module) => {
    const width = Number(module.width_mm);
    const rect = { module, x: cursor, w: width };
    cursor += width;
    return rect;
  });

  function moduleX(moduleId: string): number {
    return rects.find((rect) => rect.module.id === moduleId)?.x ?? 0;
  }

  return (
    <svg
      className="product-front-svg"
      viewBox={`${-LEFT_GUTTER} ${-TOP_GUTTER} ${totalW + LEFT_GUTTER + SIDE_GUTTER} ${height + TOP_GUTTER + BOTTOM_GUTTER}`}
      role="img"
      data-testid="product-front"
      aria-label={t("assembly.frontView")}
    >
      <SvgDim
        x={totalW / 2}
        y={-70}
        value={totalW.toFixed(2)}
        unit=" mm"
        label={t("assembly.totalWidth")}
        disabled={disabled}
        onCommit={onCommitTotalWidth}
      />
      <g transform={`rotate(-90 ${-140} ${midY})`}>
        <SvgDim
          x={-140}
          y={midY}
          value={height.toFixed(2)}
          unit=" mm"
          label={t("assembly.height")}
          disabled={disabled}
          onCommit={onCommitHeight}
        />
      </g>
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
          role="button"
          aria-label={`${t("assembly.module")} ${module.id}`}
          aria-pressed={module.id === selectedId}
          tabIndex={0}
          onClick={() => onSelectModule(module.id)}
          onKeyDown={(event) => {
            if (event.key === "Enter" || event.key === " ") {
              event.preventDefault();
              onSelectModule(module.id);
            }
          }}
        >
          <rect className="module-frame" x={x} y={0} width={w} height={height} />
          <ModuleTree
            node={module.tree}
            region={{ x: x + FRAME, y: FRAME, w: w - FRAME * 2, h: height - FRAME * 2 }}
            moduleWidth={w}
          />
        </g>
      ))}
      {selectedModule && (
        <SvgDim
          x={moduleX(selectedModule.id) + Number(selectedModule.width_mm) / 2}
          y={height + 70}
          value={Number(selectedModule.width_mm).toFixed(2)}
          unit=" mm"
          label={`${t("assembly.module")} ${selectedModule.id} ${t("assembly.width")}`}
          disabled={disabled}
          onCommit={(value) => onCommitModuleWidth(selectedModule.id, value)}
        />
      )}
    </svg>
  );
}
