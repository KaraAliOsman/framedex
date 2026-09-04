import type { EngineCalculateResponse } from "../../api/generated/models";
import type { CanvasDesignInputs } from "./canvasStore";

export type FixedPresentationGeometry = {
  nominalWidth: number;
  nominalHeight: number;
  glassWidth: number;
  glassHeight: number;
  glassX: number;
  glassY: number;
  viewBox: string;
};

export function toSvgNumber(value: string): number {
  const parsed = Number(value);
  if (!Number.isFinite(parsed) || parsed <= 0) {
    throw new Error("Technical dimension cannot be rendered");
  }
  return parsed;
}

export function fixedPresentationGeometry(
  inputs: CanvasDesignInputs,
  response: EngineCalculateResponse,
): FixedPresentationGeometry {
  const glass = response.glasses.find((piece) => piece.bay_id === inputs.parametricTree.id);
  if (glass === undefined) throw new Error("Engine response is missing the FIXED glass");

  const nominalWidth = toSvgNumber(inputs.nominalWidthMm);
  const nominalHeight = toSvgNumber(inputs.nominalHeightMm);
  const glassWidth = toSvgNumber(glass.width_mm);
  const glassHeight = toSvgNumber(glass.height_mm);
  if (glassWidth > nominalWidth || glassHeight > nominalHeight) {
    throw new Error("Engine glass does not fit the nominal presentation bounds");
  }

  const horizontalMargin = 240;
  const verticalMargin = 110;
  return {
    nominalWidth,
    nominalHeight,
    glassWidth,
    glassHeight,
    glassX: (nominalWidth - glassWidth) / 2,
    glassY: (nominalHeight - glassHeight) / 2,
    viewBox: `${-horizontalMargin} ${-verticalMargin} ${nominalWidth + horizontalMargin + 80} ${nominalHeight + verticalMargin + 80}`,
  };
}
