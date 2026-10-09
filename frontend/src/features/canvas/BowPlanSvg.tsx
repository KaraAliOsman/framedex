import {
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
  type PointerEvent,
  type RefObject,
} from "react";
import type {
  AssemblyMeasure,
  PlanGeometry,
  PlanPoint,
  ProductIssue,
} from "../../api/generated/models";
import { fmtMm, formatDecimal, parseLocaleNumber } from "../../format";
import { t } from "../../i18n/es-CL";
import { memberSurface } from "./materials";
import type { MemberGeometry } from "./members";
import type { CouplingJson, ProductModuleJson } from "./productEditing";

type BowPlanSvgProps = {
  plan: PlanGeometry;
  couplings: CouplingJson[];
  modules?: ProductModuleJson[];
  measures?: AssemblyMeasure | null;
  members: MemberGeometry;
  selectedModuleId: string | null;
  selectedCouplingId: string | null;
  issues: ProductIssue[];
  disabled: boolean;
  onSelectModule(moduleId: string): void;
  onSelectCoupling(couplingId: string): void;
  onContextMenuElement?(elementId: string, pos: { x: number; y: number }): void;
  onPreviewAngle?(couplingId: string, angleDeg: string | null): void;
  onCommitAngle(couplingId: string, angleDeg: string): void;
};

export const ANGLE_SNAPS = [0, 10, 15, 22.5, 30, 45, 90] as const;

/** Pointer coordinates are input intent, never an engineering result. */
export function snapPlanAngle(value: number): string {
  const sign = value < 0 ? -1 : 1;
  const absolute = Math.min(90, Math.abs(value));
  const snap = ANGLE_SNAPS.find((angle) => Math.abs(angle - absolute) <= 3);
  return String(sign * (snap ?? Math.round(absolute * 10) / 10));
}

/** Orient the existing engine drawing to its chord, like the front elevation.
 * This is a screen transform; engineering dimensions remain engine facts. */
export function planDisplay(plan: PlanGeometry) {
  const first = plan.front_chain[0]!,
    last = plan.front_chain.at(-1)!;
  const heading = Math.atan2(
    Number(last.y_mm) - Number(first.y_mm),
    Number(last.x_mm) - Number(first.x_mm),
  );
  const cosine = Math.cos(heading),
    sine = Math.sin(heading);
  const point = (value: PlanPoint): [number, number] => {
    const x = Number(value.x_mm) - Number(first.x_mm),
      y = Number(value.y_mm) - Number(first.y_mm);
    return [x * cosine + y * sine, x * sine - y * cosine];
  };
  const all = [
    ...plan.modules.flatMap((item) => item.corners),
    ...plan.couplings.flatMap((item) => item.polygon),
  ].map(point);
  const left = Math.min(...all.map((item) => item[0])),
    right = Math.max(...all.map((item) => item[0]));
  const top = Math.min(...all.map((item) => item[1])),
    bottom = Math.max(...all.map((item) => item[1]));
  const pad = 50;
  return {
    point,
    bounds: { x: left - pad, y: top - pad, w: right - left + pad * 2, h: bottom - top + pad * 2 },
  };
}
export function planBounds(plan: PlanGeometry) {
  return planDisplay(plan).bounds;
}
/** Text and hit targets keep screen size when the drawing is fitted. */
function usePlanScale(ref: RefObject<SVGGElement>) {
  const [scale, setScale] = useState(0.2);
  useLayoutEffect(() => {
    const element = ref.current,
      svg = element?.ownerSVGElement;
    if (!svg) return;
    const update = () => {
      const matrix = element?.getScreenCTM?.();
      if (matrix) setScale(Math.max(0.001, Math.sqrt(matrix.a * matrix.a + matrix.b * matrix.b)));
    };
    const observer = new ResizeObserver(update);
    observer.observe(svg);
    update();
    return () => observer.disconnect();
  });
  return scale;
}

function JointAngle({
  coupling,
  ordinal,
  x,
  y,
  fontSize,
  disabled,
  onSelect,
  onCommit,
  beginDrag,
}: {
  coupling: CouplingJson;
  ordinal: number;
  x: number;
  y: number;
  fontSize: number;
  disabled: boolean;
  onSelect(): void;
  onCommit(value: string): void;
  beginDrag(event: PointerEvent<SVGGElement>, onClick: () => void): void;
}) {
  const [editing, setEditing] = useState(false),
    [draft, setDraft] = useState(coupling.angle_deg),
    [invalid, setInvalid] = useState(false);
  useEffect(() => {
    if (!editing) {
      setDraft(coupling.angle_deg);
      setInvalid(false);
    }
  }, [coupling.angle_deg, editing]);
  const label = `Ángulo de unión ${ordinal}`;
  const commit = () => {
    const parsed = parseLocaleNumber(draft.replace(/[°\s]/g, ""));
    if (parsed === null || Math.abs(parsed) > 90) {
      setInvalid(true);
      return;
    }
    if (parsed !== Number(coupling.angle_deg)) onCommit(String(parsed));
    setEditing(false);
  };
  if (editing && !disabled)
    return (
      <foreignObject
        x={x - fontSize * 2.5}
        y={y - fontSize * 1.5}
        width={fontSize * 5}
        height={fontSize * 3.5}
      >
        <input
          className="canvas-dim-input"
          style={{ fontSize }}
          aria-label={label}
          aria-invalid={invalid || undefined}
          autoFocus
          inputMode="decimal"
          value={draft}
          onChange={(event) => {
            setDraft(event.target.value);
            setInvalid(false);
          }}
          onFocus={(event) => event.target.select()}
          onBlur={commit}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              event.preventDefault();
              commit();
            }
            if (event.key === "Escape") {
              event.preventDefault();
              setEditing(false);
              setDraft(coupling.angle_deg);
            }
          }}
        />
        {invalid && (
          <span className="plan-angle-error" role="alert">
            Usa un ángulo entre −90° y 90°.
          </span>
        )}
      </foreignObject>
    );
  return (
    <g
      className="plan-angle"
      data-testid={`plan-angle-${coupling.id}`}
      role="button"
      aria-label={label}
      tabIndex={disabled ? -1 : 0}
      onPointerDown={(event) => {
        if (!disabled)
          beginDrag(event, () => {
            onSelect();
            setEditing(true);
          });
      }}
      onKeyDown={(event) => {
        if (!disabled && (event.key === "Enter" || event.key === " ")) {
          event.preventDefault();
          onSelect();
          setEditing(true);
        }
      }}
    >
      <rect
        className="plan-angle-hit"
        x={x - fontSize * 2}
        y={y - fontSize * 1.25}
        width={fontSize * 4}
        height={fontSize * 2.5}
      />
      <path
        className="plan-angle-grip"
        d={`M${x - fontSize * 0.3} ${y - fontSize}l${fontSize * 0.3} ${-fontSize * 0.3}l${fontSize * 0.3} ${fontSize * 0.3}l${-fontSize * 0.3} ${fontSize * 0.3}z`}
      />
      <text x={x} y={y} fontSize={fontSize} textAnchor="middle" dominantBaseline="central">
        {formatDecimal(coupling.angle_deg, 1).replace(/,0$/, "")}°
      </text>
    </g>
  );
}

export function BowPlanContent(props: BowPlanSvgProps): JSX.Element {
  const {
    plan,
    couplings,
    modules,
    measures,
    members,
    selectedModuleId,
    selectedCouplingId,
    issues,
    disabled,
    onSelectModule,
    onSelectCoupling,
    onContextMenuElement,
    onPreviewAngle,
    onCommitAngle,
  } = props;
  const ref = useRef<SVGGElement>(null),
    detach = useRef<(() => void) | null>(null);
  const scale = usePlanScale(ref),
    fontSize = 13 / scale;
  const display = planDisplay(plan);
  const polygonPoints = (points: PlanPoint[]) =>
    points.map((item) => display.point(item).join(",")).join(" ");
  const footprintKey = (points: PlanPoint[]) =>
    points.map((item) => `${Number(item.x_mm)},${Number(item.y_mm)}`).join(" ");
  const center = (points: PlanPoint[]) =>
    points
      .map(display.point)
      .reduce<[number, number]>(
        (sum, item) => [sum[0] + item[0] / points.length, sum[1] + item[1] / points.length],
        [0, 0],
      );
  useEffect(() => () => detach.current?.(), []);
  const flagged = new Set(
    issues
      .filter((issue) => issue.target.startsWith("coupling:"))
      .map((issue) => issue.target.slice(9)),
  );
  function beginDrag(
    event: PointerEvent<SVGElement>,
    coupling: CouplingJson,
    pivot: [number, number],
    click: () => void,
  ) {
    if (disabled || event.button !== 0) return;
    event.preventDefault();
    event.stopPropagation();
    detach.current?.();
    const matrix = ref.current?.getScreenCTM?.();
    if (!matrix) return;
    const inverse = matrix.inverse();
    const point = (clientX: number, clientY: number) =>
      new DOMPoint(clientX, clientY).matrixTransform(inverse);
    const start = point(event.clientX, event.clientY);
    const startAngle = Math.atan2(-(start.y - pivot[1]), start.x - pivot[0]);
    const pointerId = event.pointerId;
    let moved = false,
      last = coupling.angle_deg;
    const move = (next: globalThis.PointerEvent) => {
      if (next.pointerId !== pointerId) return;
      if (!moved && Math.hypot(next.clientX - event.clientX, next.clientY - event.clientY) < 3)
        return;
      const current = point(next.clientX, next.clientY);
      if (!current) return;
      moved = true;
      let delta =
        ((Math.atan2(-(current.y - pivot[1]), current.x - pivot[0]) - startAngle) * 180) / Math.PI;
      if (delta > 180) delta -= 360;
      if (delta < -180) delta += 360;
      const value = snapPlanAngle(Math.max(-90, Math.min(90, Number(coupling.angle_deg) + delta)));
      if (value !== last) {
        last = value;
        onPreviewAngle?.(coupling.id, value);
      }
    };
    const stop = () => {
      window.removeEventListener("pointermove", move);
      window.removeEventListener("pointerup", up);
      window.removeEventListener("pointercancel", cancel);
      detach.current = null;
    };
    const cancel = () => {
      stop();
      onPreviewAngle?.(coupling.id, null);
    };
    const up = (next: globalThis.PointerEvent) => {
      if (next.pointerId !== pointerId) return;
      stop();
      if (moved) {
        onCommitAngle(coupling.id, last);
        onPreviewAngle?.(coupling.id, null);
      } else click();
    };
    detach.current = cancel;
    window.addEventListener("pointermove", move);
    window.addEventListener("pointerup", up);
    window.addEventListener("pointercancel", cancel);
  }
  return (
    <g ref={ref} className="bow-plan-content" data-testid="bow-plan">
      {plan.modules.map((module, index) => {
        const ordinal = (modules?.findIndex((item) => item.id === module.module_id) ?? index) + 1;
        const incoming =
          couplings.find((c) => c.kind !== "STACKED" && c.modules?.[1] === module.module_id) ??
          (index > 0
            ? couplings.filter((c) => !c.modules && c.kind !== "STACKED")[index - 1]
            : undefined);
        const origin = incoming
          ? plan.couplings.find((c) => c.coupling_id === incoming.id)?.polygon[0]
          : undefined;
        const [x, y] = center(module.corners);
        const coincident = plan.modules.filter(
          (item) => footprintKey(item.corners) === footprintKey(module.corners),
        );
        const showLabel = coincident[0]?.module_id === module.module_id;
        const moduleLabel = coincident
          .map(
            (item) =>
              `M${(modules?.findIndex((entry) => entry.id === item.module_id) ?? plan.modules.indexOf(item)) + 1}`,
          )
          .join(" / ");
        const value =
          measures?.modules.find((item) => item.module_id === module.module_id)?.width_mm ??
          modules?.find((item) => item.id === module.module_id)?.width_mm;
        return (
          <g key={module.module_id}>
            <polygon
              className={`plan-module${module.module_id === selectedModuleId ? " is-selected" : ""}`}
              style={{ fill: memberSurface(members.frame.material).fill }}
              points={polygonPoints(module.corners)}
              role="button"
              aria-label={`Módulo ${ordinal} en planta`}
              aria-pressed={module.module_id === selectedModuleId}
              tabIndex={0}
              onPointerDown={(event) => {
                if (incoming && origin && !disabled)
                  beginDrag(event, incoming, display.point(origin), () =>
                    onSelectModule(module.module_id),
                  );
                else onSelectModule(module.module_id);
              }}
              onContextMenu={(event) => {
                if (onContextMenuElement) {
                  event.preventDefault();
                  onContextMenuElement(module.module_id, { x: event.clientX, y: event.clientY });
                }
              }}
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();
                  onSelectModule(module.module_id);
                }
              }}
            />
            {showLabel && (
              <text
                className="plan-module-number"
                x={x}
                y={y + fontSize * 2}
                fontSize={fontSize}
                textAnchor="middle"
                pointerEvents="none"
              >
                {moduleLabel} · {value ? `${fmtMm(value)} mm` : "Sin dato"}
              </text>
            )}
          </g>
        );
      })}
      {plan.couplings.map((coupling) => {
        const spec = couplings.find((item) => item.id === coupling.coupling_id);
        if (!spec) return null;
        const [x, y] = center(coupling.polygon),
          pivot = display.point(coupling.polygon[0]!);
        const ordinal = couplings.findIndex((item) => item.id === spec.id) + 1;
        return (
          <g
            key={coupling.coupling_id}
            className={flagged.has(spec.id) ? "plan-joint has-issue" : "plan-joint"}
          >
            <polygon
              className={`plan-coupling${spec.id === selectedCouplingId ? " is-selected" : ""}`}
              points={polygonPoints(coupling.polygon)}
              data-testid={`plan-coupling-${spec.id}`}
              role="button"
              aria-label={`Unión ${ordinal} en planta`}
              tabIndex={0}
              onClick={() => onSelectCoupling(spec.id)}
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();
                  onSelectCoupling(spec.id);
                }
              }}
            />
            {spec.kind !== "STACKED" && (
              <JointAngle
                coupling={spec}
                ordinal={ordinal}
                x={x}
                y={y - fontSize * 2}
                fontSize={fontSize}
                disabled={disabled}
                onSelect={() => onSelectCoupling(spec.id)}
                onCommit={(value) => onCommitAngle(spec.id, value)}
                beginDrag={(event, click) => beginDrag(event, spec, pivot, click)}
              />
            )}
            {flagged.has(spec.id) && (
              <text
                className="plan-issue-flag"
                x={x}
                y={y + fontSize * 3.5}
                fontSize={fontSize}
                textAnchor="middle"
              >
                Revisar unión {ordinal}
              </text>
            )}
          </g>
        );
      })}
      <polyline
        className="plan-front-chain"
        points={plan.front_chain.map((point) => display.point(point).join(",")).join(" ")}
        fill="none"
        pointerEvents="none"
      />
    </g>
  );
}

export function BowPlanSvg(props: BowPlanSvgProps): JSX.Element {
  const bounds = planBounds(props.plan);
  return (
    <svg
      className="bow-plan-svg"
      viewBox={`${bounds.x} ${bounds.y} ${bounds.w} ${bounds.h}`}
      role="img"
      aria-label={t("assembly.planView")}
    >
      <title>{t("assembly.planView")}</title>
      <BowPlanContent {...props} />
    </svg>
  );
}
