import { fmtMm } from "../../format";

type Authority = {
  family_name: string;
  class_name: string;
  source: string;
  synthetic: boolean;
  components: {
    name: string;
    source: string;
    quantity: {
      base: number;
      axis?: string | null;
      threshold?: string;
      step?: string;
      increment?: number;
    };
    length?: { axis: string; fixed_mm?: string; deduction_mm: string } | null;
  }[];
};
const axes: Record<string, string> = {
  WIDTH: "ancho",
  HEIGHT: "alto",
  PERIMETER: "perímetro",
  WEIGHT: "masa sin herraje",
  FIXED: "largo fijo",
};

export function HardwareAuthorityView({ value }: { value: unknown }): JSX.Element {
  const authority = value as Authority;
  return (
    <fieldset className="catalog-group catalog-hardware-authority">
      <legend>Familia y reglas de clase</legend>
      <p>
        <strong>
          {authority.family_name} · {authority.class_name}
        </strong>
        {authority.synthetic ? " · DEMO, sin certificación" : ""}
      </p>
      <p>Fuente: {authority.source}</p>
      <p>
        Modifica las reglas con la plantilla de catálogo. Revisa el diff antes de publicar; la
        revisión emitida conserva su autoridad.
      </p>
      <ul>
        {authority.components.map((component, index) => (
          <li key={index}>
            <strong>{component.name}</strong>
            <p className="catalog-hardware-rule">
              {component.quantity.base} unidades declaradas
              {component.quantity.axis
                ? ` + ${component.quantity.increment ?? "Sin dato"} por cada ${fmtMm(component.quantity.step)} ${component.quantity.axis === "WEIGHT" ? "kg" : "mm"} de ${axes[component.quantity.axis]} sobre ${fmtMm(component.quantity.threshold)} ${component.quantity.axis === "WEIGHT" ? "kg" : "mm"}`
                : ""}
              .
              {component.length
                ? ` Largo: ${component.length.axis === "FIXED" ? `${fmtMm(component.length.fixed_mm)} mm` : axes[component.length.axis]} − ${fmtMm(component.length.deduction_mm)} mm.`
                : ""}
            </p>
            <details>
              <summary>Fuente del componente</summary>
              <p>{component.source}</p>
            </details>
          </li>
        ))}
      </ul>
    </fieldset>
  );
}
