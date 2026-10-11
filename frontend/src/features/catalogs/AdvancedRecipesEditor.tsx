import { decimalInputValue } from "../../decimal";
import type { AdvancedRecipe, Capability } from "../canvas/physicalOpenings";
import { domainLabel } from "../../i18n/domainLabels";

const dimensions = [
  ["inset_left_mm", "Retiro izquierdo · mm"],
  ["inset_right_mm", "Retiro derecho · mm"],
  ["inset_top_mm", "Retiro superior · mm"],
  ["inset_bottom_mm", "Retiro inferior · mm"],
  ["meeting_overlap_mm", "Traslape del encuentro · mm"],
  ["meeting_gap_mm", "Separación del encuentro · mm"],
  ["glazing_deduction_width_mm", "Descuento de vidrio en ancho · mm"],
  ["glazing_deduction_height_mm", "Descuento de vidrio en alto · mm"],
  ["rail_end_deduction_mm", "Descuento de extremos de guía · mm"],
  ["interlock_end_deduction_mm", "Descuento de encuentro corredero · mm"],
  ["opening_angle_deg", "Ángulo abierto · grados"],
  ["min_leaf_width_mm", "Ancho mínimo de hoja · mm"],
  ["max_leaf_width_mm", "Ancho máximo de hoja · mm"],
  ["min_leaf_height_mm", "Alto mínimo de hoja · mm"],
  ["max_leaf_height_mm", "Alto máximo de hoja · mm"],
  ["max_leaf_weight_kg", "Peso máximo de hoja · kg"],
  ["starter_width_mm", "Ancho inicial del esquema · mm"],
  ["starter_height_mm", "Alto inicial del esquema · mm"],
] as const;
type Panel = {
  slot: string;
  kind: "MOVING" | "FIXED";
  share: string;
  fixed_in_sash: boolean;
  track: number | null;
  plane_offset_mm: string;
  travel: string | null;
  travel_fraction: string;
  closing_side: string;
  pivot_fraction: string | null;
  fold_group: string | null;
  fold_index: number | null;
  stack_side: string | null;
  pass_through: boolean;
  balance: string | null;
};
type Authority = AdvancedRecipe &
  Record<(typeof dimensions)[number][0], string> & {
    schema_version: 1;
    distribution_axis: string;
    panels: Panel[];
    leaf_profile_role: string;
    threshold_height_mm: string | null;
    rail_profile_role: string | null;
    rail_count: number;
    rail_sides: string[];
    interlock_required: boolean;
    lift_mm: string | null;
    parallel_offset_mm: string | null;
    packet_pitch_mm: string | null;
    hardware_kit_skus: string[];
    pass_through_hardware_kit_skus: string[];
  };

/** Only authored source values. Empty measures never become engineering defaults. */
export function AdvancedRecipesEditor({
  capability,
  onChange,
}: {
  capability: Capability;
  onChange(recipes: AdvancedRecipe[]): void;
}): JSX.Element {
  const recipes = (capability.advanced_recipes ?? []) as Authority[];
  const patch = (at: number, values: Partial<Authority>) =>
    onChange(recipes.map((recipe, index) => (index === at ? { ...recipe, ...values } : recipe)));
  const text = (label: string, value: string, update: (value: string) => void, numeric = false) => (
    <label>
      <span>{label}</span>
      <input
        value={value}
        inputMode={numeric ? "decimal" : "text"}
        onChange={(event) =>
          update(numeric ? decimalInputValue(event.target.value) : event.target.value)
        }
      />
    </label>
  );
  const select = (
    label: string,
    value: string | null,
    choices: [string, string][],
    update: (value: string) => void,
  ) => (
    <label>
      <span>{label}</span>
      <select value={value ?? ""} onChange={(event) => update(event.target.value)}>
        <option value="">Sin dato / no corresponde</option>
        {choices.map(([key, name]) => (
          <option key={key} value={key}>
            {name}
          </option>
        ))}
      </select>
    </label>
  );
  const optional = (label: string, value: string | null, update: (value: string | null) => void) =>
    text(label, value ?? "", (value) => update(value || null), true);
  const kitList = (
    at: number,
    recipe: Authority,
    field: "hardware_kit_skus" | "pass_through_hardware_kit_skus",
    label: string,
  ) => (
    <fieldset className="catalog-group">
      <legend>{label}</legend>
      {capability.hardware_kit_skus.map((sku) => (
        <label key={sku}>
          <input
            type="checkbox"
            checked={recipe[field]?.includes(sku) ?? false}
            onChange={(event) =>
              patch(at, {
                [field]: event.target.checked
                  ? [...(recipe[field] ?? []), sku]
                  : recipe[field].filter((value) => value !== sku),
              })
            }
          />
          {sku}
        </label>
      ))}
    </fieldset>
  );
  return (
    <fieldset className="catalog-group">
      <legend>Esquemas avanzados con fuente</legend>
      <p>
        Declare las medidas, perfiles y movimientos desde el documento del fabricante. El motor
        valida la composición y sus herrajes al guardar.
      </p>
      {recipes.map((recipe, at) => (
        <details key={at} open={!recipe.code}>
          <summary>{recipe.name || `Esquema ${at + 1} sin completar`}</summary>
          <div className="catalog-fields">
            {text("Código del esquema", recipe.code, (code) => patch(at, { code }))}
            {text("Nombre para el estimador", recipe.name, (name) => patch(at, { name }))}
            {text("Composición (A, C, 3+0…)", recipe.scheme, (scheme) => patch(at, { scheme }))}
            {text("Documento, página y revisión de fuente", recipe.source, (source) =>
              patch(at, { source }),
            )}
            {select(
              "Distribución de paneles",
              recipe.distribution_axis,
              [
                ["X", "Izquierda a derecha"],
                ["Y", "Arriba a abajo"],
              ],
              (distribution_axis) => patch(at, { distribution_axis }),
            )}
            {select(
              "Perfil de hoja",
              recipe.leaf_profile_role,
              ["SASH", "SLIDING_SASH", "DOOR_SASH"].map((role) => [role, domainLabel(role)]),
              (leaf_profile_role) => patch(at, { leaf_profile_role }),
            )}
            {dimensions.map(([key, label]) => (
              <span key={key}>
                {text(label, recipe[key], (value) => patch(at, { [key]: value }), true)}
              </span>
            ))}
            {optional("Altura del umbral · mm", recipe.threshold_height_mm, (threshold_height_mm) =>
              patch(at, { threshold_height_mm }),
            )}
            {optional("Elevación de HST · mm", recipe.lift_mm, (lift_mm) => patch(at, { lift_mm }))}
            {optional("Separación de PSK · mm", recipe.parallel_offset_mm, (parallel_offset_mm) =>
              patch(at, { parallel_offset_mm }),
            )}
            {optional(
              "Espesor de paquete plegado · mm",
              recipe.packet_pitch_mm,
              (packet_pitch_mm) => patch(at, { packet_pitch_mm }),
            )}
            <label>
              <input
                type="checkbox"
                checked={recipe.synthetic}
                onChange={(event) => patch(at, { synthetic: event.target.checked })}
              />
              Autoridad sintética · DEMO sin certificación
            </label>
            <label>
              <input
                type="checkbox"
                checked={recipe.interlock_required}
                onChange={(event) => patch(at, { interlock_required: event.target.checked })}
              />
              Requiere encuentro corredero
            </label>
          </div>
          <fieldset className="catalog-group">
            <legend>Guías y bordes</legend>
            {recipe.rail_sides.map((side, index) => (
              <div key={index}>
                {select(
                  `Borde de guía ${index + 1}`,
                  side,
                  [
                    ["TOP", "Superior"],
                    ["BOTTOM", "Inferior"],
                    ["LEFT", "Izquierdo"],
                    ["RIGHT", "Derecho"],
                  ],
                  (value) =>
                    patch(at, {
                      rail_sides: recipe.rail_sides.map((old, i) => (i === index ? value : old)),
                    }),
                )}
                <button
                  type="button"
                  onClick={() => {
                    const rail_sides = recipe.rail_sides.filter((_, i) => i !== index);
                    patch(at, {
                      rail_sides,
                      rail_count: rail_sides.length,
                      rail_profile_role: rail_sides.length ? "RAIL" : null,
                    });
                  }}
                >
                  Quitar guía {index + 1}
                </button>
              </div>
            ))}
            <button
              type="button"
              onClick={() =>
                patch(at, {
                  rail_sides: [...recipe.rail_sides, ""],
                  rail_count: recipe.rail_sides.length + 1,
                  rail_profile_role: "RAIL",
                })
              }
            >
              Agregar guía desde fuente
            </button>
          </fieldset>
          {kitList(at, recipe, "hardware_kit_skus", "Herrajes del esquema")}
          {kitList(at, recipe, "pass_through_hardware_kit_skus", "Herrajes de hoja de paso")}
          {recipe.panels.map((panel, index) => {
            const change = (values: Partial<Panel>) =>
              patch(at, {
                panels: recipe.panels.map((old, i) => (i === index ? { ...old, ...values } : old)),
              });
            return (
              <fieldset className="catalog-group" key={index}>
                <legend>Panel {index + 1} · orden de vista interior</legend>
                <div className="catalog-fields">
                  {text("Dirección de hoja", panel.slot, (slot) => change({ slot }))}
                  {select(
                    "Función",
                    panel.kind,
                    [
                      ["MOVING", "Hoja móvil"],
                      ["FIXED", "Paño fijo"],
                    ],
                    (kind) => change({ kind: kind as Panel["kind"] }),
                  )}
                  {text(
                    "Proporción exacta del vano",
                    panel.share,
                    (share) => change({ share }),
                    true,
                  )}
                  {text(
                    "Plano desde referencia · mm",
                    panel.plane_offset_mm,
                    (plane_offset_mm) => change({ plane_offset_mm }),
                    true,
                  )}
                  {select(
                    "Carril",
                    panel.track === null ? null : String(panel.track),
                    Array.from({ length: 16 }, (_, i) => [String(i), `Carril ${i + 1}`]),
                    (value) => change({ track: value === "" ? null : Number(value) }),
                  )}
                  {select(
                    "Recorrido",
                    panel.travel,
                    [
                      ["LEFT", "A la izquierda"],
                      ["RIGHT", "A la derecha"],
                      ["UP", "Hacia arriba"],
                      ["DOWN", "Hacia abajo"],
                    ],
                    (value) => change({ travel: value || null }),
                  )}
                  {text(
                    "Fracción exacta del recorrido",
                    panel.travel_fraction,
                    (travel_fraction) => change({ travel_fraction }),
                    true,
                  )}
                  {select(
                    "Borde de cierre",
                    panel.closing_side,
                    [
                      ["NONE", "Paño fijo"],
                      ["LEFT", "Izquierdo"],
                      ["RIGHT", "Derecho"],
                      ["TOP", "Superior"],
                      ["BOTTOM", "Inferior"],
                    ],
                    (closing_side) => change({ closing_side }),
                  )}
                  {optional("Fracción de eje pivotante", panel.pivot_fraction, (pivot_fraction) =>
                    change({ pivot_fraction }),
                  )}
                  {text("Grupo de paquete", panel.fold_group ?? "", (value) =>
                    change({ fold_group: value || null }),
                  )}
                  {select(
                    "Orden desde anclaje",
                    panel.fold_index === null ? null : String(panel.fold_index),
                    Array.from({ length: 16 }, (_, i) => [String(i), String(i + 1)]),
                    (value) => change({ fold_index: value === "" ? null : Number(value) }),
                  )}
                  {select(
                    "Lado del paquete",
                    panel.stack_side,
                    [
                      ["LEFT", "Izquierdo"],
                      ["RIGHT", "Derecho"],
                    ],
                    (value) => change({ stack_side: value || null }),
                  )}
                  {select(
                    "Balance de guillotina",
                    panel.balance,
                    [
                      ["SPRING", "Muelles"],
                      ["COUNTERWEIGHT", "Contrapesos"],
                    ],
                    (value) => change({ balance: value || null }),
                  )}
                  <label>
                    <input
                      type="checkbox"
                      checked={panel.fixed_in_sash}
                      onChange={(event) => change({ fixed_in_sash: event.target.checked })}
                    />
                    Fijo en hoja
                  </label>
                  <label>
                    <input
                      type="checkbox"
                      checked={panel.pass_through}
                      onChange={(event) => change({ pass_through: event.target.checked })}
                    />
                    Hoja de paso independiente
                  </label>
                </div>
                <button
                  type="button"
                  onClick={() => patch(at, { panels: recipe.panels.filter((_, i) => i !== index) })}
                >
                  Quitar panel {index + 1}
                </button>
              </fieldset>
            );
          })}
          <button
            type="button"
            onClick={() =>
              patch(at, {
                panels: [
                  ...recipe.panels,
                  {
                    slot: "",
                    kind: "MOVING",
                    share: "",
                    fixed_in_sash: false,
                    track: null,
                    plane_offset_mm: "",
                    travel: null,
                    travel_fraction: "",
                    closing_side: "NONE",
                    pivot_fraction: null,
                    fold_group: null,
                    fold_index: null,
                    stack_side: null,
                    pass_through: false,
                    balance: null,
                  },
                ],
              })
            }
          >
            Agregar panel desde fuente
          </button>
          <button
            type="button"
            onClick={() => onChange(recipes.filter((_, index) => index !== at))}
          >
            Quitar esquema {at + 1}
          </button>
        </details>
      ))}
      <button
        type="button"
        onClick={() =>
          onChange([
            ...recipes,
            {
              ...(Object.fromEntries(dimensions.map(([key]) => [key, ""])) as Record<
                (typeof dimensions)[number][0],
                string
              >),
              schema_version: 1,
              code: "",
              starter_width_mm: "",
              starter_height_mm: "",
              name: "",
              scheme: "",
              source: "",
              synthetic: false,
              distribution_axis: "",
              panels: [],
              leaf_profile_role: "",
              threshold_height_mm: null,
              rail_profile_role: null,
              rail_count: 0,
              rail_sides: [],
              interlock_required: false,
              lift_mm: null,
              parallel_offset_mm: null,
              packet_pitch_mm: null,
              hardware_kit_skus: [],
              pass_through_hardware_kit_skus: [],
            } as Authority,
          ])
        }
      >
        Agregar esquema desde fuente
      </button>
    </fieldset>
  );
}
