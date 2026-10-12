import { domainLabel, domainLabels } from "../../i18n/domainLabels";

const causes: Record<string, string> = {
  measure_ungrounded:
    "La medida no está declarada ni respaldada por el motor. Indica la medida que quieres usar.",
  operation_schema_invalid:
    "La propuesta tiene parámetros incompletos. Vuelve a pedir el cambio con el diseño actual.",
  simulation_invalid: "El motor rechaza la geometría propuesta. Revisa las medidas y la apertura.",
  opening_incompatible:
    "La serie no admite esa apertura. Elige una serie compatible en el catálogo.",
  unobserved_ref:
    "La posición todavía no fue consultada. Abre la posición y vuelve a pedir el cambio.",
  tool_budget_exceeded: "El trabajo agotó sus consultas. Divide la petición y vuelve a intentar.",
  proposal_stale: "El diseño cambió después de la propuesta. Vuelve a simular antes de aplicar.",
  installation_height_required:
    "Falta la altura del antepecho desde el piso. Declárala antes de ubicar la manilla.",
  travel_not_supported:
    "La serie no declara recorrido editable. Revisa los carriles en el catálogo.",
};

export function RejectedOperations({
  items,
}: {
  items: { op?: string | null; reason?: string }[];
}): JSX.Element {
  return (
    <div className="ask-dock__warnings">
      <ul>
        {items.map((item, index) => (
          <li key={index}>
            {item.op && item.op in domainLabels ? `${domainLabel(item.op)}: ` : "Cambio: "}
            {causes[item.reason ?? ""] ??
              "No se aplicó el cambio. Revisa la serie, las medidas y los datos del catálogo; luego vuelve a simular."}
          </li>
        ))}
      </ul>
      <details>
        <summary>Detalles técnicos</summary>
        <pre>{JSON.stringify(items, null, 2)}</pre>
      </details>
    </div>
  );
}
