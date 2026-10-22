import { useState } from "react";
import { fmtMm } from "../../format";
import type { OpeningLeafFact } from "./physicalOpenings";

/** Screen projection of sealed engine points, without deriving travel or axes. */
export function AdvancedPlanPane({
  facts,
  onHide,
}: {
  facts: Record<string, OpeningLeafFact[]>;
  onHide(): void;
}): JSX.Element {
  const [passage, setPassage] = useState(false);
  const rows = Object.entries(facts).flatMap(([module, leaves]) => {
    const bays = [...new Set(leaves.filter((leaf) => leaf.advanced).map((leaf) => leaf.bay_id))];
    return bays.map((bay) => ({
      key: `${module}-${bay}`,
      leaves: leaves.filter((leaf) => leaf.bay_id === bay && leaf.advanced),
    }));
  });
  return (
    <section className="advanced-plan-pane" aria-label="Planta de aperturas avanzadas">
      <header>
        <h2>Planta · recorrido del motor</h2>
        {rows.some((row) => row.leaves.some((leaf) => leaf.advanced?.pass_through)) && (
          <button
            type="button"
            aria-pressed={passage}
            onClick={() => setPassage((value) => !value)}
          >
            {passage ? "Ver paquete plegado" : "Ver hoja de paso"}
          </button>
        )}
        <button type="button" onClick={onHide}>
          Ocultar planta
        </button>
      </header>
      <p className="advanced-plan-legend">
        Línea discontinua: hoja cerrada · Línea continua: hoja abierta
      </p>
      {rows.map(({ key, leaves }) => {
        const passageBay = passage && leaves.some((leaf) => leaf.advanced!.pass_open_plan);
        const points = leaves.flatMap((leaf) => [
          ...leaf.advanced!.closed_plan,
          ...(!passageBay ? (leaf.advanced!.open_plan_polygon ?? []) : []),
          ...(passageBay
            ? (leaf.advanced!.pass_open_plan ?? leaf.advanced!.closed_plan)
            : leaf.advanced!.open_plan),
        ]);
        const xs = points.map((point) => Number(point.x_mm)),
          depths = points.map((point) => Number(point.depth_mm));
        const minX = Math.min(...xs),
          maxX = Math.max(...xs),
          minDepth = Math.min(...depths),
          maxDepth = Math.max(...depths);
        const span = maxX - minX,
          pad = Math.max(span / 25, 50);
        const path = (values: typeof points) =>
          values
            .map((point, index) => `${index ? "L" : "M"}${point.x_mm} ${point.depth_mm}`)
            .join(" ");
        return (
          <figure key={key}>
            <figcaption>{leaves[0]!.advanced!.recipe_name} · Vista desde arriba</figcaption>
            <svg
              viewBox={`${minX - pad} ${minDepth - pad} ${span + pad * 2} ${Math.max(maxDepth - minDepth, pad * 2) + pad * 2}`}
              role="img"
              aria-label={`Planta de ${leaves[0]!.advanced!.recipe_name}`}
            >
              {leaves.map((leaf) => {
                const data = leaf.advanced!;
                return (
                  <g key={leaf.leaf_id ?? leaf.bay_id} data-plan-leaf={leaf.leaf_id}>
                    <title>
                      {data.kind === "FIXED"
                        ? "Paño fijo"
                        : data.pass_through && passageBay
                          ? "Hoja de paso independiente"
                          : data.track != null
                            ? `Carril ${data.track + 1} · recorrido ${fmtMm(data.travel_mm)} mm`
                            : "Recorrido con eje declarado"}
                    </title>
                    <path
                      className="advanced-plan-closed"
                      d={path(data.closed_plan)}
                      vectorEffect="non-scaling-stroke"
                    />
                    <path
                      className="advanced-plan-open"
                      d={path(
                        passageBay ? (data.pass_open_plan ?? data.closed_plan) : data.open_plan,
                      )}
                      vectorEffect="non-scaling-stroke"
                    />
                    {!passageBay && Boolean(data.open_plan_polygon?.length) && (
                      <path
                        className="advanced-plan-open"
                        d={`${path(data.open_plan_polygon!)} Z`}
                        vectorEffect="non-scaling-stroke"
                      />
                    )}
                    {data.pivot_x_mm != null && (
                      <circle
                        className="advanced-plan-axis"
                        cx={data.pivot_x_mm}
                        cy={data.plane_offset_mm}
                        r={pad / 8}
                      />
                    )}
                  </g>
                );
              })}
            </svg>
            <details>
              <summary>¿De dónde sale el recorrido?</summary>
              <p>{leaves[0]!.advanced!.source}</p>
              <ul>
                {leaves
                  .filter((leaf) => leaf.advanced!.kind === "MOVING")
                  .map((leaf, index) => (
                    <li key={leaf.leaf_id}>
                      Hoja {index + 1}
                      {leaf.advanced!.track != null ? ` · carril ${leaf.advanced!.track + 1}` : ""}
                      {leaf.advanced!.travel
                        ? ` · recorrido ${fmtMm(leaf.advanced!.travel_mm)} mm`
                        : ""}
                      {leaf.advanced!.lift_mm
                        ? ` · elevación ${fmtMm(leaf.advanced!.lift_mm)} mm`
                        : ""}
                      {leaf.advanced!.parallel_offset_mm
                        ? ` · separación paralela ${fmtMm(leaf.advanced!.parallel_offset_mm)} mm`
                        : ""}
                      {leaf.advanced!.packet_pitch_mm
                        ? ` · espesor de paquete ${fmtMm(leaf.advanced!.packet_pitch_mm)} mm`
                        : ""}
                      {leaf.advanced!.balance
                        ? ` · ${leaf.advanced!.balance === "SPRING" ? "muelles" : "contrapesos"}`
                        : ""}
                      {leaf.advanced!.pivot_y_mm
                        ? ` · eje horizontal ${fmtMm(leaf.advanced!.pivot_y_mm)} mm desde arriba`
                        : ""}
                    </li>
                  ))}
              </ul>
            </details>
          </figure>
        );
      })}
    </section>
  );
}
