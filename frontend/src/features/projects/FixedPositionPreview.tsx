import type { EngineCalculateResponse } from "../../api/generated/models";
import { t } from "../../i18n/es-CL";
import type { CanvasDesignInputs } from "../canvas/canvasStore";
import { topIntent } from "../canvas/intentEditing";
import { fixedPresentationGeometry } from "../canvas/presentationGeometry";
import "../canvas/canvas.css";

type Props = {
  inputs: CanvasDesignInputs;
  result: EngineCalculateResponse | null;
  children?: JSX.Element;
};

export function FixedPositionPreview({ inputs, result, children }: Props): JSX.Element | null {
  if (result === null) return children ?? null;

  let geometry;
  const glass = result.glasses[0];

  try {
    const bay = topIntent(inputs.parametricTree);
    if (
      bay.type !== "BAY" ||
      bay.opening_type !== "FIXED" ||
      (bay.children?.length ?? 0) !== 0 ||
      result.glasses.length !== 1 ||
      result.panels.length !== 0 ||
      glass === undefined ||
      glass.bay_id !== bay.id ||
      glass.leaf_id !== null
    ) {
      return children ?? null;
    }

    geometry = fixedPresentationGeometry({ ...inputs, parametricTree: bay }, result);
  } catch {
    return children ?? null;
  }

  return (
    <figure data-testid="fixed-position-preview">
      <svg
        className="cad-svg position-fixed-svg"
        viewBox={geometry.viewBox}
        preserveAspectRatio="xMidYMid meet"
        role="img"
        aria-label={t("intent.fixed")}
      >
        <title>{t("intent.fixed")}</title>
        <rect
          className="frame-outline"
          data-testid="position-preview-frame"
          x="0"
          y="0"
          width={geometry.nominalWidth}
          height={geometry.nominalHeight}
        />
        <rect
          className="glass-pane"
          data-testid="position-preview-glass"
          x={geometry.glassX}
          y={geometry.glassY}
          width={geometry.glassWidth}
          height={geometry.glassHeight}
          data-width-mm={glass.width_mm}
          data-height-mm={glass.height_mm}
        />
      </svg>
      <figcaption>
        {glass.width_mm} × {glass.height_mm} mm
      </figcaption>
    </figure>
  );
}
