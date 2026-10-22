import { fmtMm } from "../../format";
import { domainLabels } from "../../i18n/domainLabels";

const names: Record<string, string> = {
  profile_cuts: "Perfiles",
  reinforcements: "Refuerzos",
  glasses: "Vidrios",
  panels: "Paneles",
  fittings: "Uniones",
  hardware_items: "Herrajes",
  leaf_weights: "Pesos de hojas",
  opening_leaves: "Aperturas de hojas",
  finish: "Acabado",
  extras: "Complementos",
  extra_suggestions: "Complementos propuestos",
  sku: "Código",
  article_sku: "Código",
  parent_profile_sku: "Perfil",
  role: "Función",
  qty: "Cantidad",
  quantity: "Cantidad",
  unit: "Unidad",
  length_mm: "Largo · mm",
  width_mm: "Ancho · mm",
  height_mm: "Alto · mm",
  angle_left: "Ángulo izquierdo · °",
  angle_right: "Ángulo derecho · °",
  area_m2: "Área · m²",
  weight_kg: "Peso · kg",
  total_weight_kg: "Peso total · kg",
  glass_spec: "Composición del vidrio",
  glass_thickness_mm: "Espesor del vidrio · mm",
  node_id: "Hoja",
  leaf_id: "Hoja",
  opening_type: "Apertura",
  type: "Tipo",
  material: "Material",
  resolution: "Composición",
  components: "Componentes",
  kit_sku: "Kit",
  source_ref: "Referencia",
  source_refs: "Referencias",
  name: "Nombre",
};
type Difference = { path: string; field: string; before: unknown; after: unknown };
function differences(before: unknown, after: unknown, path = "", field = ""): Difference[] {
  if (JSON.stringify(before) === JSON.stringify(after)) return [];
  const a =
    before !== null && typeof before === "object" ? (before as Record<string, unknown>) : null;
  const b = after !== null && typeof after === "object" ? (after as Record<string, unknown>) : null;
  if (a || b)
    return [...new Set([...Object.keys(a ?? {}), ...Object.keys(b ?? {})])].flatMap((key) =>
      differences(
        a?.[key],
        b?.[key],
        `${path}${path ? " · " : ""}${/^\d+$/.test(key) ? Number(key) + 1 : (names[key] ?? key.replaceAll("_", " "))}`,
        key,
      ),
    );
  return [{ path, field, before, after }];
}
function value(item: unknown, field: string): string {
  if (item === undefined) return "No existe";
  if (item === null) return "No aplica";
  if (typeof item === "boolean") return item ? "Sí" : "No";
  if (
    typeof item === "number" ||
    (typeof item === "string" &&
      /(_mm|_kg|_m2|_kg_m)$|^angle_|^(qty|quantity)$/.test(field) &&
      /^-?\d+(\.\d+)?$/.test(item))
  )
    return fmtMm(String(item));
  return domainLabels[String(item)] ?? String(item);
}

/** Read-only projection of the entire physical snapshot; never calculates a result. */
export function ReferenceOutputChanges({
  before,
  after,
}: {
  before: unknown;
  after: unknown;
}): JSX.Element | null {
  const rows = differences(before, after);
  if (!rows.length) return null;
  return (
    <details className="series-trial__details">
      <summary>Ver todos los cambios del despiece ({rows.length})</summary>
      <div
        className="series-trial__scroll"
        role="region"
        aria-label="Detalle completo del cambio"
        tabIndex={0}
      >
        <table className="series-trial__table">
          <thead>
            <tr>
              <th>Dato</th>
              <th>Antes</th>
              <th>Después</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.path} data-changed="true">
                <th scope="row">{row.path}</th>
                <td>{value(row.before, row.field)}</td>
                <td>{value(row.after, row.field)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </details>
  );
}
