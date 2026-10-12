import type { SystemDimensionalLimitRequest } from "../../api/generated/models";
import { SystemDimensionalLimitOpeningTypeEnum } from "../../api/generated/models";
import { t } from "../../i18n/es-CL";
import { OPENING_OPTIONS } from "../canvas/openings";

export const compatibleOpenings = (family: string): string[] => {
  const fixed = ["FIXED"];
  if (family === "CASEMENT")
    return [...fixed, "TURN_LEFT", "TURN_RIGHT", "TILT_TURN_LEFT", "TILT_TURN_RIGHT", "AWNING"];
  if (["SLIDING", "LIFT_SLIDE"].includes(family))
    return [...fixed, "SLIDING", "SLIDING_2L", "SLIDING_3L", "SLIDING_4L"];
  if (family === "DOOR") return [...fixed, "DOOR_ENTRY", "DOOR_DOUBLE"];
  return fixed;
};
const labels = {
  min_leaf_width_mm: "Ancho mínimo de hoja (mm)",
  max_leaf_width_mm: "Ancho máximo de hoja (mm)",
  min_leaf_height_mm: "Alto mínimo de hoja (mm)",
  max_leaf_height_mm: "Alto máximo de hoja (mm)",
  max_leaf_weight_kg: "Peso máximo de hoja (kg)",
  min_aspect_ratio: "Relación alto/ancho mínima",
  max_aspect_ratio: "Relación alto/ancho máxima",
  source: "Fuente del límite",
};
export function CatalogLimitsEditor({
  family,
  limits,
  onChange,
}: {
  family: string;
  limits: SystemDimensionalLimitRequest[];
  onChange: (limits: SystemDimensionalLimitRequest[]) => void;
}): JSX.Element {
  function patch(index: number, field: string, value: string) {
    onChange(
      limits.map((limit, current) =>
        current === index
          ? {
              ...limit,
              [field]:
                field === "source"
                  ? value
                  : field === "max_leaf_weight_kg" && !value.trim()
                    ? null
                    : value.replace(",", "."),
            }
          : limit,
      ),
    );
  }
  return (
    <fieldset className="catalog-group">
      <legend>Límites dimensionales y fuente</legend>
      {!limits.length && (
        <p>
          Sin dato: declara los límites del proveedor por apertura antes de calcular productos
          nuevos.
        </p>
      )}
      {limits.map((limit, index) => (
        <fieldset className="catalog-group" key={index}>
          <legend>Límite de hoja {index + 1}</legend>
          <div className="catalog-fields">
            <label>
              Apertura
              <select
                value={String(limit.opening_type)}
                onChange={(event) => patch(index, "opening_type", event.target.value)}
              >
                {Object.values(SystemDimensionalLimitOpeningTypeEnum)
                  .filter(
                    (opening) =>
                      compatibleOpenings(family).includes(opening) ||
                      opening === limit.opening_type,
                  )
                  .map((opening) => (
                    <option value={opening} key={opening}>
                      {opening === "DOOR_DOUBLE"
                        ? "Puerta doble"
                        : t(
                            OPENING_OPTIONS.find(([value]) => value === opening)?.[1] ??
                              "intent.fixed",
                          )}
                    </option>
                  ))}
              </select>
            </label>
            {Object.entries(labels).map(([field, label]) => (
              <label key={field}>
                {label}
                <input
                  type="text"
                  inputMode={field === "source" ? undefined : "decimal"}
                  placeholder="Sin dato"
                  value={limit[field as keyof typeof limit] ?? ""}
                  onChange={(event) => patch(index, field, event.target.value)}
                />
              </label>
            ))}
          </div>
          <button
            type="button"
            onClick={() => onChange(limits.filter((_, current) => current !== index))}
          >
            Quitar límite
          </button>
        </fieldset>
      ))}
      <button
        type="button"
        onClick={() =>
          onChange([
            ...limits,
            {
              opening_type: "FIXED",
              min_leaf_width_mm: "",
              max_leaf_width_mm: "",
              min_leaf_height_mm: "",
              max_leaf_height_mm: "",
              max_leaf_weight_kg: null,
              min_aspect_ratio: "",
              max_aspect_ratio: "",
              source: "",
            },
          ])
        }
      >
        Agregar límite de apertura
      </button>
    </fieldset>
  );
}
