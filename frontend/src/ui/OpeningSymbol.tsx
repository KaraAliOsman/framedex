import type { PhysicalOpening } from "../features/canvas/physicalOpenings";
import { openingSymbolLines, symbolPath } from "./openingSymbols";

/** DIN motion lines shared by the palette, technical canvas and documents. */
export function OpeningSymbol({
  opening,
  x,
  y,
  width,
  height,
  view = "interior",
  travel,
  mirror = true,
  axis,
}: {
  opening: PhysicalOpening;
  x: number;
  y: number;
  width: number;
  height: number;
  view?: "interior" | "exterior";
  travel?: "LEFT" | "RIGHT" | "UP" | "DOWN" | null;
  mirror?: boolean;
  axis?: { x?: number | null; y?: number | null; closingSide?: string };
}): JSX.Element {
  const lines = openingSymbolLines(opening, { x, y, width, height }, view, travel, mirror, axis);
  return (
    <g
      className="opening-glyph"
      data-motion={opening.movement}
      data-hinge={opening.hinge_side}
      data-direction={opening.direction}
      data-leaf-role={opening.leaf_role}
      fill="none"
    >
      {lines.map((line) => (
        <path
          key={line.symbol}
          data-symbol={line.symbol.startsWith("turn_") ? "turn" : line.symbol}
          d={symbolPath(line)}
          strokeWidth="1.5"
          vectorEffect="non-scaling-stroke"
          strokeDasharray={line.dashed ? "6 4" : undefined}
        />
      ))}
    </g>
  );
}
