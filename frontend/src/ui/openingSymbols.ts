import type { PhysicalOpening } from "../features/canvas/physicalOpenings";
import { symbolMotions, symbolTemplates } from "./openingSymbols.generated";

export type SymbolLine = { symbol: string; points: [number, number][]; dashed: boolean };

export function legacySymbolOpening(kind: string, doorHinge?: "LEFT" | "RIGHT"): PhysicalOpening {
  return {
    movement:
      kind === "TILT"
        ? "TILT"
        : kind.startsWith("TILT")
          ? "TILT_TURN"
          : kind.startsWith("TURN") || kind.startsWith("DOOR")
            ? "TURN"
            : kind === "AWNING"
              ? "TOP_HUNG"
              : kind.startsWith("SLIDING")
                ? "SLIDE"
                : "FIXED",
    hinge_side:
      kind === "TILT"
        ? "BOTTOM"
        : kind === "AWNING"
          ? "TOP"
          : kind.endsWith("LEFT")
            ? "LEFT"
            : kind.endsWith("RIGHT")
              ? "RIGHT"
              : kind.startsWith("DOOR")
                ? (doorHinge ?? "NONE")
                : "NONE",
    direction: kind === "AWNING" ? "OUTWARD" : "INWARD",
    leaf_role: "SINGLE",
    fixed_in_sash: false,
  };
}

/** Projection of the engine-generated grammar. Never calculates manufacturing data. */
export function openingSymbolLines(
  opening: PhysicalOpening,
  rect: { x: number; y: number; width: number; height: number },
  view: "interior" | "exterior" = "interior",
  travel?: "LEFT" | "RIGHT" | "UP" | "DOWN" | null,
  mirror = true,
  axis?: { x?: number | null; y?: number | null; closingSide?: string },
): SymbolLine[] {
  // Apply integer ratios from the generated Decimal grammar. Multiplying by
  // a binary approximation of 0.35 would produce 489.999… instead of 490 mm.
  const coordinate = (origin: number, extent: number, ratio: string, invert = false): number => {
    const [whole = "0", fraction = ""] = ratio.split(".");
    const denominator = 10 ** fraction.length;
    const numerator = Number(whole + fraction);
    return origin + (extent * (invert ? denominator - numerator : numerator)) / denominator;
  };
  const key = `${opening.movement}/${["LEFT", "RIGHT"].includes(opening.hinge_side) ? opening.hinge_side : "NONE"}/${travel ?? ""}`;
  const names =
    opening.movement === "FOLD" && axis?.closingSide === "LEFT"
      ? (["fold_right"] as const)
      : (symbolMotions[key] ?? []);
  const sliding = ["SLIDE", "LIFT_SLIDE", "PARALLEL_SLIDE", "VERTICAL_SLIDE"].includes(
    opening.movement,
  );
  return names.map((symbol) => ({
    symbol,
    points: symbolTemplates[symbol].map(([px, py]) => [
      symbol === "pivot_v" && axis?.x != null
        ? view === "exterior" && mirror
          ? rect.x * 2 + rect.width - axis.x
          : axis.x
        : coordinate(rect.x, rect.width, px, view === "exterior" && mirror),
      symbol === "pivot_h" && axis?.y != null ? axis.y : coordinate(rect.y, rect.height, py),
    ]),
    dashed: !sliding && (opening.direction === "OUTWARD") !== (view === "exterior"),
  }));
}

export function symbolPath(line: SymbolLine): string {
  return line.points.map(([x, y], i) => `${i === 0 ? "M" : "L"}${x} ${y}`).join("");
}
