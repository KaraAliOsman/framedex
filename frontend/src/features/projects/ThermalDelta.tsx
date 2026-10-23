import { formatDecimal } from "../../format";
import type { ThermalMetric } from "./thermalModel";

export function ThermalDelta({ simulation }: { simulation: unknown }) {
  const delta = (
    simulation as {
      thermal_delta?: {
        before: ThermalMetric | null;
        after: ThermalMetric | null;
        delta_uw: string | null;
      };
    } | null
  )?.thermal_delta;
  if (!delta)
    return <p>Δ de Uw: Falta completar · esta propuesta no contiene un cálculo térmico.</p>;
  const causes = [...new Set([...(delta.before?.missing ?? []), ...(delta.after?.missing ?? [])])];
  return (
    <div className="thermal-readout">
      <p className="project-number">
        Uw {delta.before?.uw == null ? "Falta completar" : formatDecimal(delta.before.uw, 2)} →{" "}
        {delta.after?.uw == null ? "Falta completar" : formatDecimal(delta.after.uw, 2)} W/m²K · Δ{" "}
        {delta.delta_uw == null ? "Falta completar" : `${formatDecimal(delta.delta_uw, 2)} W/m²K`}
      </p>
      {delta.delta_uw == null ? (
        <p>{causes.join(" ") || "Ambos lados requieren un cálculo autoritativo del motor."}</p>
      ) : (
        <p>
          ISO 10077-1 · diferencia entre los cálculos del motor antes y después, con sus áreas y
          referencias revisadas.
        </p>
      )}
    </div>
  );
}
