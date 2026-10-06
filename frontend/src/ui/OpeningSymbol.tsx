import type { PhysicalOpening } from "../features/canvas/physicalOpenings";

/** DIN motion lines shared by the palette, technical canvas and documents. */
export function OpeningSymbol({
  opening,
  x,
  y,
  width,
  height,
  view = "interior",
}: {
  opening: PhysicalOpening;
  x: number;
  y: number;
  width: number;
  height: number;
  view?: "interior" | "exterior";
}): JSX.Element {
  const left = x + width * 0.2,
    right = x + width * 0.8;
  const top = y + height * 0.2,
    bottom = y + height * 0.8;
  const middleX = x + width / 2,
    middleY = y + height / 2;
  const hingeLeft = (opening.hinge_side === "LEFT") !== (view === "exterior");
  const away = (opening.direction === "OUTWARD") !== (view === "exterior");
  return (
    <g
      className="opening-glyph"
      data-motion={opening.movement}
      data-hinge={opening.hinge_side}
      data-direction={opening.direction}
      data-leaf-role={opening.leaf_role}
      strokeDasharray={away ? "6 4" : undefined}
      fill="none"
    >
      {["TURN", "TILT_TURN"].includes(opening.movement) && (
        <path
          data-symbol="turn"
          d={
            hingeLeft
              ? `M${left} ${top}L${right} ${middleY}L${left} ${bottom}`
              : `M${right} ${top}L${left} ${middleY}L${right} ${bottom}`
          }
        />
      )}
      {["TILT", "TILT_TURN"].includes(opening.movement) && (
        <path data-symbol="tilt" d={`M${left} ${bottom}L${middleX} ${top}L${right} ${bottom}`} />
      )}
      {opening.movement === "TOP_HUNG" && (
        <path data-symbol="awning" d={`M${left} ${top}L${middleX} ${bottom}L${right} ${top}`} />
      )}
      {opening.movement === "SLIDE" && (
        <path
          data-symbol="slide"
          d={`M${left} ${middleY}H${right}M${right - width * 0.1} ${middleY - height * 0.06}L${right} ${middleY}L${right - width * 0.1} ${middleY + height * 0.06}`}
        />
      )}
    </g>
  );
}
