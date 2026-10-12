import type { ProfileSection } from "../../api/generated/models";
import { SectionPreviewSvg } from "../canvas/SectionPreviewSvg";

type Section = {
  source?: string;
  depth_mm?: string;
  orientation?: string;
  local_origin?: string;
  polygon?: Array<{ x_mm: string; y_mm: string }>;
  axes?: Array<{ name: string; y_mm: string }>;
};
export function ImportedSectionFields({
  value,
  onChange,
}: {
  value: unknown;
  onChange: (next: unknown) => void;
}) {
  const section = value && typeof value === "object" ? (value as Section) : null;
  if (!section)
    return (
      <div>
        <p>Sección: Sin dato. Contrasta el dibujo y su unidad antes de declarar las coordenadas.</p>
        <button
          type="button"
          onClick={() => onChange({ source: "POLYGON", polygon: [], axes: [] })}
        >
          Declarar sección desde la fuente
        </button>
      </div>
    );
  const patch = (field: keyof Section, next: unknown) => onChange({ ...section, [field]: next });
  return (
    <div className="catalog-import-section">
      <label>
        Profundidad declarada (mm)
        <input
          value={section.depth_mm ?? ""}
          inputMode="decimal"
          onChange={(event) => patch("depth_mm", event.target.value)}
        />
      </label>
      <label>
        Exterior de la sección
        <select
          value={section.orientation ?? ""}
          onChange={(event) => patch("orientation", event.target.value)}
        >
          <option value="">Sin dato</option>
          {Object.entries({
            EXTERIOR_DOWN: "Abajo",
            EXTERIOR_UP: "Arriba",
            EXTERIOR_LEFT: "Izquierda",
            EXTERIOR_RIGHT: "Derecha",
          }).map(([key, label]) => (
            <option key={key} value={key}>
              {label}
            </option>
          ))}
        </select>
      </label>
      <label>
        Origen local
        <select
          value={section.local_origin ?? ""}
          onChange={(event) => patch("local_origin", event.target.value)}
        >
          <option value="">Sin dato</option>
          {Object.entries({
            TOP_LEFT: "Superior izquierdo",
            TOP_RIGHT: "Superior derecho",
            BOTTOM_LEFT: "Inferior izquierdo",
            BOTTOM_RIGHT: "Inferior derecho",
            CENTROID: "Centroide",
          }).map(([key, label]) => (
            <option key={key} value={key}>
              {label}
            </option>
          ))}
        </select>
      </label>
      <p>Coordenadas del contorno en mm, en orden alrededor de la sección.</p>
      {(section.polygon ?? []).map((point, index) => (
        <div key={index} className="catalog-section-point">
          <label>
            Vértice {index + 1} · X (mm)
            <input
              inputMode="decimal"
              value={point.x_mm}
              onChange={(event) =>
                patch(
                  "polygon",
                  section.polygon?.map((item, at) =>
                    at === index ? { ...item, x_mm: event.target.value } : item,
                  ),
                )
              }
            />
          </label>
          <label>
            Y (mm)
            <input
              inputMode="decimal"
              value={point.y_mm}
              onChange={(event) =>
                patch(
                  "polygon",
                  section.polygon?.map((item, at) =>
                    at === index ? { ...item, y_mm: event.target.value } : item,
                  ),
                )
              }
            />
          </label>
          <button
            type="button"
            onClick={() =>
              patch(
                "polygon",
                section.polygon?.filter((_, at) => at !== index),
              )
            }
          >
            Quitar vértice {index + 1}
          </button>
        </div>
      ))}
      <button
        type="button"
        onClick={() => patch("polygon", [...(section.polygon ?? []), { x_mm: "", y_mm: "" }])}
      >
        Agregar vértice
      </button>
      {section.polygon &&
      section.polygon.length >= 3 &&
      section.polygon.every(
        (point) => /^-?\d+(?:\.\d+)?$/.test(point.x_mm) && /^-?\d+(?:\.\d+)?$/.test(point.y_mm),
      ) ? (
        <SectionPreviewSvg section={section as ProfileSection} faceWidthMm={0} />
      ) : null}
      <button type="button" onClick={() => onChange(null)}>
        Dejar sección sin dato
      </button>
    </div>
  );
}
