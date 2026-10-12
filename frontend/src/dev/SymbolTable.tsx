import cases from "../../../engine/tests/fixtures/symbols/cases.json";
import contours from "../../../engine/tests/fixtures/symbols/contours.json";
import { OpeningSymbol } from "../ui/OpeningSymbol";
import type { PhysicalOpening } from "../features/canvas/physicalOpenings";
import { contourPathD, insetContourPoints, pointsPathD } from "../features/canvas/contourGeometry";
import type { ContourJson } from "../features/canvas/productEditing";

/** DEV only: the same frozen fixtures exercised by the Python and TS renderers. */
export function SymbolTable(): JSX.Element {
  return (
    <section className="symbol-table" aria-label="Contrato completo de simbología">
      <p>
        Casos de referencia · vista declarada y manilla. Los diagramas reservados no habilitan
        fabricación.
      </p>
      <div className="symbol-table__grid">
        {cases.map((fixture) => (
          <figure key={fixture.name} data-symbol-case={fixture.name}>
            <svg viewBox="-80 -80 1360 1560" role="img" aria-label={fixture.name}>
              <g
                transform={
                  fixture.view === "exterior" ? "translate(1200 0) scale(-1 1)" : undefined
                }
              >
                {fixture.leaves.map((leaf, index) => (
                  <g key={index}>
                    <rect
                      className="symbol-table__frame"
                      x={Number(leaf.x_mm)}
                      y="0"
                      width={Number(leaf.width_mm)}
                      height="1400"
                    />
                    <OpeningSymbol
                      opening={leaf.opening as PhysicalOpening}
                      x={Number(leaf.x_mm)}
                      y={Number(leaf.y_mm)}
                      width={Number(leaf.width_mm)}
                      height={Number(leaf.height_mm)}
                      view={fixture.view as "interior" | "exterior"}
                      mirror={false}
                      travel={leaf.travel as "LEFT" | "RIGHT" | null}
                    />
                    {leaf.handle && (
                      <circle
                        className="symbol-table__handle"
                        cx={Number(leaf.x_mm) + Number(leaf.handle.x_mm)}
                        cy={Number(leaf.handle.y_mm)}
                        r="18"
                      />
                    )}
                  </g>
                ))}
              </g>
            </svg>
            <figcaption>
              {fixture.label} · Vista {fixture.view === "interior" ? "interior" : "exterior"}
            </figcaption>
          </figure>
        ))}
        {contours.map((fixture) => (
          <figure key={fixture.name}>
            <svg viewBox="-80 -700 1360 1780" role="img" aria-label={fixture.name}>
              <path
                className="symbol-table__frame"
                d={contourPathD(fixture.contour as ContourJson, 1000)}
              />
              <path
                className="symbol-table__glass"
                d={pointsPathD(insetContourPoints(fixture.contour as ContourJson, 40), 1000)}
              />
            </svg>
            <figcaption>{fixture.name} · Vista interior</figcaption>
          </figure>
        ))}
      </div>
    </section>
  );
}
