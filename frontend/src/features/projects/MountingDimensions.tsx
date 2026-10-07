import { fmtMm } from "../../format";
import { useViewportScale } from "../canvas/CanvasViewport";
import { frontLayout } from "../canvas/ProductFrontSvg";
import type { ProductJson } from "../canvas/productEditing";
import type { MountingEvidence } from "./mountingModel";
import "./mounting.css";

export function MountingDimensions({
  product,
  evidence,
}: {
  product: ProductJson;
  evidence: MountingEvidence[];
}) {
  const layout = frontLayout(product);
  const scale = useViewportScale();
  const fontSize = Math.max(34, 12 / scale);
  return (
    <g className="mounting-dimensions" aria-label="Cota doble de vano y fabricación">
      {evidence.map((item) => {
        const rect = layout.rects.find((r) => r.module.id === item.survey.module_id);
        if (!rect) return null;
        const top = layout.lift + layout.height - rect.sill - rect.h;
        const openingWidth = Number(item.result.width.opening_mm),
          openingHeight = Number(item.result.height.opening_mm);
        const left = rect.x + Number(item.result.width.first_adjustment_mm);
        const openingTop = top + Number(item.result.height.second_adjustment_mm);
        const fabricationLabelY = Math.min(top, openingTop) - fontSize;
        const openingLabelY = fabricationLabelY - fontSize * 1.7;
        const dimensionY = openingLabelY + fontSize * 0.35;
        const tick = fontSize * 0.2;
        return (
          <g key={item.survey.module_id}>
            <rect x={left} y={openingTop} width={openingWidth} height={openingHeight} />
            <line x1={left} x2={left + openingWidth} y1={dimensionY} y2={dimensionY} />
            <line x1={left} x2={left} y1={dimensionY - tick} y2={dimensionY + tick} />
            <line
              x1={left + openingWidth}
              x2={left + openingWidth}
              y1={dimensionY - tick}
              y2={dimensionY + tick}
            />
            <text x={rect.x + rect.w / 2} y={openingLabelY} style={{ fontSize }}>
              Vano {fmtMm(item.result.width.opening_mm)} × {fmtMm(item.result.height.opening_mm)} mm
            </text>
            <text x={rect.x + rect.w / 2} y={fabricationLabelY} style={{ fontSize }}>
              Fabricación {fmtMm(rect.module.width_mm)} × {fmtMm(rect.module.height_mm)} mm
            </text>
          </g>
        );
      })}
    </g>
  );
}
