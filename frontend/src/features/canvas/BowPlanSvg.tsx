import type { PlanGeometry, PlanPoint } from "../../api/generated/models";

type BowPlanSvgProps = {
  plan: PlanGeometry;
  selectedModuleId: string | null;
  onSelectModule(moduleId: string): void;
};

const PAD_MM = 220;

function toSvg(point: PlanPoint): [number, number] {
  // Engine y grows upward; SVG y grows downward — mirror vertically so a
  // positive coupling angle reads as the bow curving up on screen.
  return [Number(point.x_mm), -Number(point.y_mm)];
}

function polygonPoints(points: PlanPoint[]): string {
  return points.map((point) => toSvg(point).join(",")).join(" ");
}

function midpoint(a: PlanPoint, b: PlanPoint): [number, number] {
  return [(Number(a.x_mm) + Number(b.x_mm)) / 2, -(Number(a.y_mm) + Number(b.y_mm)) / 2];
}

export function BowPlanSvg({
  plan,
  selectedModuleId,
  onSelectModule,
}: BowPlanSvgProps): JSX.Element {
  const minX = Number(plan.min_x_mm) - PAD_MM;
  const minY = -(Number(plan.min_y_mm) + Number(plan.height_mm)) - PAD_MM;
  const width = Number(plan.width_mm) + PAD_MM * 2;
  const height = Number(plan.height_mm) + PAD_MM * 2;
  const fontSize = Math.max(width, height) * 0.035;
  const dimOffset = Math.max(width, height) * 0.06;
  const chain = plan.front_chain;

  return (
    <svg
      className="bow-plan-svg"
      viewBox={`${minX} ${minY} ${width} ${height}`}
      role="img"
      data-testid="bow-plan"
    >
      {plan.modules.map((module) => (
        <polygon
          key={module.module_id}
          className={
            module.module_id === selectedModuleId ? "plan-module is-selected" : "plan-module"
          }
          points={polygonPoints(module.corners)}
          data-testid={`plan-module-${module.module_id}`}
          onClick={() => onSelectModule(module.module_id)}
        />
      ))}
      {plan.couplings.map((coupling) => (
        <polygon
          key={coupling.coupling_id}
          className="plan-coupling"
          points={polygonPoints(coupling.polygon)}
        />
      ))}
      <polyline
        className="plan-front-chain"
        points={chain.map((point) => toSvg(point).join(",")).join(" ")}
        fill="none"
      />
      {chain.slice(0, -1).map((point, index) => {
        const next = chain[index + 1];
        if (!next) return null;
        const [mx, my] = midpoint(point, next);
        const segmentLength = Math.hypot(
          Number(next.x_mm) - Number(point.x_mm),
          Number(next.y_mm) - Number(point.y_mm),
        );
        const normalX = -(Number(next.y_mm) - Number(point.y_mm)) / segmentLength;
        const normalY = (Number(next.x_mm) - Number(point.x_mm)) / segmentLength;
        return (
          <text
            key={`dim-${index}`}
            className="plan-dimension"
            x={mx + normalX * dimOffset}
            y={my - normalY * dimOffset}
            fontSize={fontSize}
            textAnchor="middle"
          >
            {Math.round(segmentLength)}
          </text>
        );
      })}
      <text
        className="plan-dimension plan-dimension--total"
        x={Number(plan.min_x_mm) + Number(plan.width_mm) / 2}
        y={-(Number(plan.min_y_mm) + Number(plan.height_mm)) - fontSize}
        fontSize={fontSize}
        textAnchor="middle"
      >
        {Math.round(Number(plan.width_mm))} mm
      </text>
    </svg>
  );
}
