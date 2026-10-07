import type { FinishAuthority, FinishColor, FinishCombination } from "../../api/generated/models";
import { decimalInputValue } from "../../decimal";
import { finishColorCss } from "../canvas/finishColors";

export const finishProcessNames: Record<string, string> = {
  MASS: "PVC en masa",
  FOIL: "Foliado",
  COEXTRUDED: "Coextruido",
  RAL: "Lacado RAL",
  ANODIZED: "Anodizado",
  WOOD_EFFECT: "Efecto madera",
};

export function finishAuthorityProblem(value: FinishAuthority | null): string | null {
  if (!value) return null;
  if (!value.source.trim()) return "Carta de colores: falta la fuente del fabricante.";
  if (!value.colors.length || !value.combinations.length)
    return "Carta de colores: declara colores y al menos una combinación permitida.";
  for (const color of [...value.colors, ...(value.handle_colors ?? [])]) {
    if (
      ![color.code, color.manufacturer_code, color.name, color.source, ...color.linear_rgb].every(
        (v) => v.trim(),
      )
    )
      return "Color: completa su identidad, los tres canales lineales y la fuente.";
  }
  for (const combo of value.combinations) {
    if (
      ![
        combo.code,
        combo.interior,
        combo.exterior,
        combo.reinforcement_stock_code,
        combo.glass_clearance_mm,
        combo.source,
        combo.surcharge.amount,
        combo.surcharge.source,
      ].every((v) => v.trim())
    )
      return "Combinación: completa caras, stock de refuerzo, holgura, recargo y fuentes.";
    if (value.material === "PVC" && !combo.base)
      return "Combinación PVC: declara el color de masa de la base.";
  }
  return null;
}

/** Sourced authority: empty dimensions and prices remain missing until entered. */
export function FinishAuthorityEditor({
  value,
  material,
  onChange,
}: {
  value: FinishAuthority | null;
  material: string;
  onChange(value: FinishAuthority | null): void;
}): JSX.Element {
  function patchColor(index: number, patch: Partial<FinishColor>) {
    if (value)
      onChange({
        ...value,
        colors: value.colors.map((c, i) => (i === index ? { ...c, ...patch } : c)),
      });
  }
  function patchCombo(index: number, patch: Partial<FinishCombination>) {
    if (value)
      onChange({
        ...value,
        combinations: value.combinations.map((c, i) => (i === index ? { ...c, ...patch } : c)),
      });
  }
  const input = (
    label: string,
    current: string | null,
    edit: (v: string) => void,
    decimal = false,
  ) => (
    <label>
      <span>{label}</span>
      <input
        value={decimal ? decimalInputValue(current ?? "") : (current ?? "")}
        placeholder="Sin dato"
        inputMode={decimal ? "decimal" : undefined}
        onChange={(e) => edit(decimal ? e.target.value.replace(",", ".") : e.target.value)}
      />
    </label>
  );
  const flag = (label: string, current: boolean, edit: (v: boolean) => void) => (
    <label>
      <span>{label}</span>
      <select value={String(current)} onChange={(e) => edit(e.target.value === "true")}>
        <option value="true">Sí</option>
        <option value="false">No</option>
      </select>
    </label>
  );
  const face = (label: string, current: string | null, edit: (v: string) => void, base = false) => (
    <label>
      <span>{label}</span>
      <select value={current ?? ""} onChange={(e) => edit(e.target.value)}>
        <option value="">Sin dato</option>
        {value?.colors
          .filter((c) => !base || c.kind === "MASS")
          .map((c, i) => (
            <option key={i} value={c.code}>
              {c.name || "Color sin nombre"}
            </option>
          ))}
      </select>
    </label>
  );
  return (
    <fieldset className="catalog-group finish-authority">
      <legend>Carta de colores y acabados</legend>
      <p>
        Declara las muestras y las combinaciones de la fuente. Las caras comparten una identidad de
        compra; el acero conserva su propio acabado. Los campos vacíos siguen Sin dato.
      </p>
      {!value ? (
        <>
          <p>Sin carta por caras. La serie conserva sus acabados históricos.</p>
          <button
            type="button"
            onClick={() =>
              onChange({ schema_version: 1, material, source: "", colors: [], combinations: [] })
            }
          >
            Declarar carta desde una fuente
          </button>
        </>
      ) : (
        <>
          {input("Fuente de la carta", value.source, (source) => onChange({ ...value, source }))}
          {value.material !== material && (
            <p role="alert">
              El material de la carta no coincide con la serie. Revise la fuente y vuelva a declarar
              la carta.
            </p>
          )}
          <h4>Muestras del fabricante</h4>
          {value.colors.map((color, index) => (
            <details key={index} className="catalog-group">
              <summary>
                <span
                  className="finish-swatch"
                  style={{
                    backgroundColor: color.linear_rgb.every((v) => v !== "")
                      ? finishColorCss(color)
                      : undefined,
                  }}
                  aria-hidden="true"
                />{" "}
                {color.name || `Color ${index + 1}`} · {finishProcessNames[color.kind]}
                {color.synthetic ? " · DEMO" : ""}
                {color.approximate ? " · aproximado" : ""}
              </summary>
              <div className="catalog-fields">
                {input("Código en la carta", color.code, (code) => patchColor(index, { code }))}
                {input("Código del fabricante", color.manufacturer_code, (manufacturer_code) =>
                  patchColor(index, { manufacturer_code }),
                )}
                {input("Nombre comercial", color.name, (name) => patchColor(index, { name }))}
                <label>
                  <span>Proceso</span>
                  <select
                    value={color.kind}
                    onChange={(e) => patchColor(index, { kind: e.target.value })}
                  >
                    {(value.material === "PVC"
                      ? ["MASS", "FOIL", "COEXTRUDED"]
                      : ["RAL", "ANODIZED", "WOOD_EFFECT"]
                    ).map((kind) => (
                      <option value={kind} key={kind}>
                        {finishProcessNames[kind]}
                      </option>
                    ))}
                  </select>
                </label>
                {color.linear_rgb.map((channel, n) =>
                  input(
                    `Canal lineal ${["rojo", "verde", "azul"][n]} (0 a 1)`,
                    channel,
                    (next) =>
                      patchColor(index, {
                        linear_rgb: color.linear_rgb.map((v, i) => (i === n ? next : v)),
                      }),
                    true,
                  ),
                )}
                {input(
                  "Brillo (0 a 1; vacío si no se declara)",
                  color.gloss,
                  (gloss) => patchColor(index, { gloss: gloss || null }),
                  true,
                )}
                {input(
                  "Textura local del catálogo (si existe)",
                  color.texture_path,
                  (texture_path) => patchColor(index, { texture_path: texture_path || null }),
                )}
                {flag("Muestra aproximada", color.approximate, (approximate) =>
                  patchColor(index, { approximate }),
                )}
                {flag("Datos sintéticos DEMO", color.synthetic, (synthetic) =>
                  patchColor(index, { synthetic }),
                )}
                {input("Fuente de la muestra", color.source, (source) =>
                  patchColor(index, { source }),
                )}
              </div>
              <button
                type="button"
                onClick={() =>
                  onChange({ ...value, colors: value.colors.filter((_, i) => i !== index) })
                }
              >
                Quitar muestra
              </button>
            </details>
          ))}
          <button
            type="button"
            onClick={() =>
              onChange({
                ...value,
                colors: [
                  ...value.colors,
                  {
                    code: "",
                    manufacturer_code: "",
                    name: "",
                    kind: value.material === "PVC" ? "MASS" : "RAL",
                    linear_rgb: ["", "", ""],
                    gloss: null,
                    texture_path: null,
                    approximate: true,
                    source: "",
                    synthetic: false,
                  },
                ],
              })
            }
          >
            Agregar muestra
          </button>
          <h4>Combinaciones permitidas y reglas</h4>
          <details className="catalog-group">
            <summary>Muestras de manillas y herrajes</summary>
            <p>
              Solo se ofrecen los colores compatibles declarados en la clase de herraje. Sin
              muestra, el render conserva el herraje esquemático.
            </p>
            {(value.handle_colors ?? []).map((color, index) => {
              const edit = (patch: Partial<FinishColor>) =>
                onChange({
                  ...value,
                  handle_colors: value.handle_colors?.map((c, i) =>
                    i === index ? { ...c, ...patch } : c,
                  ),
                });
              return (
                <fieldset className="catalog-group" key={index}>
                  <legend>{color.name || `Manilla ${index + 1}`}</legend>
                  <div className="catalog-fields">
                    {input("Código compatible de manilla", color.code, (code) => edit({ code }))}
                    {input(
                      "Código del fabricante de manilla",
                      color.manufacturer_code,
                      (manufacturer_code) => edit({ manufacturer_code }),
                    )}
                    {input("Nombre de la muestra de manilla", color.name, (name) => edit({ name }))}
                    {color.linear_rgb.map((channel, n) =>
                      input(
                        `Canal lineal de manilla ${["rojo", "verde", "azul"][n]} (0 a 1)`,
                        channel,
                        (next) =>
                          edit({
                            linear_rgb: color.linear_rgb.map((v, i) => (i === n ? next : v)),
                          }),
                        true,
                      ),
                    )}
                    {input("Fuente de la muestra de manilla", color.source, (source) =>
                      edit({ source }),
                    )}
                    {flag("Manilla aproximada", color.approximate, (approximate) =>
                      edit({ approximate }),
                    )}
                    {flag("Muestra de manilla DEMO", color.synthetic, (synthetic) =>
                      edit({ synthetic }),
                    )}
                  </div>
                  <button
                    type="button"
                    onClick={() =>
                      onChange({
                        ...value,
                        handle_colors: value.handle_colors?.filter((_, i) => i !== index),
                      })
                    }
                  >
                    Quitar muestra de manilla
                  </button>
                </fieldset>
              );
            })}
            <button
              type="button"
              onClick={() =>
                onChange({
                  ...value,
                  handle_colors: [
                    ...(value.handle_colors ?? []),
                    {
                      code: "",
                      manufacturer_code: "",
                      name: "",
                      kind: "RAL",
                      linear_rgb: ["", "", ""],
                      gloss: null,
                      texture_path: null,
                      approximate: true,
                      synthetic: false,
                      source: "",
                    },
                  ],
                })
              }
            >
              Agregar muestra de manilla
            </button>
          </details>
          {value.combinations.map((combo, index) => (
            <details key={index} className="catalog-group">
              <summary>
                {value.colors.find((c) => c.code === combo.exterior)?.name || "Exterior sin dato"}{" "}
                exterior /{" "}
                {value.colors.find((c) => c.code === combo.interior)?.name || "Interior sin dato"}{" "}
                interior{combo.synthetic ? " · DEMO" : ""}
              </summary>
              <div className="catalog-fields">
                {input("Identidad de stock y compra", combo.code, (code) =>
                  patchCombo(index, { code }),
                )}
                {face("Interior", combo.interior, (interior) => patchCombo(index, { interior }))}
                {face("Exterior", combo.exterior, (exterior) => patchCombo(index, { exterior }))}
                {value.material === "PVC" &&
                  face(
                    "Base en masa",
                    combo.base,
                    (base) => patchCombo(index, { base: base || null }),
                    true,
                  )}
                {flag(
                  "Refuerzo obligatorio",
                  combo.reinforcement_required,
                  (reinforcement_required) => patchCombo(index, { reinforcement_required }),
                )}
                {input(
                  "Acabado de stock del acero",
                  combo.reinforcement_stock_code,
                  (reinforcement_stock_code) => patchCombo(index, { reinforcement_stock_code }),
                )}
                {input(
                  "Holgura de vidrio (mm)",
                  combo.glass_clearance_mm,
                  (glass_clearance_mm) => patchCombo(index, { glass_clearance_mm }),
                  true,
                )}
                {(
                  [
                    "max_position_width_mm",
                    "max_position_height_mm",
                    "max_leaf_width_mm",
                    "max_leaf_height_mm",
                  ] as const
                ).map((field, n) =>
                  input(
                    [
                      "Ancho máximo de posición (mm)",
                      "Alto máximo de posición (mm)",
                      "Ancho máximo de hoja (mm)",
                      "Alto máximo de hoja (mm)",
                    ][n]!,
                    combo[field],
                    (next) => patchCombo(index, { [field]: next || null }),
                    true,
                  ),
                )}
                <label>
                  <span>Días adicionales (vacío: Sin dato)</span>
                  <input
                    value={combo.extra_lead_days ?? ""}
                    inputMode="numeric"
                    onChange={(e) => {
                      if (/^\d*$/.test(e.target.value))
                        patchCombo(index, {
                          extra_lead_days: e.target.value === "" ? null : Number(e.target.value),
                        });
                    }}
                  />
                </label>
                <label>
                  <span>Regla de recargo</span>
                  <select
                    value={combo.surcharge.kind}
                    onChange={(e) =>
                      patchCombo(index, { surcharge: { ...combo.surcharge, kind: e.target.value } })
                    }
                  >
                    {Object.entries({
                      NONE: "Sin recargo declarado",
                      PER_M: "Por metro de perfil",
                      PERCENT: "Porcentaje del costo de perfiles",
                      FIXED: "Fijo por posición",
                    }).map(([key, label]) => (
                      <option key={key} value={key}>
                        {label}
                      </option>
                    ))}
                  </select>
                </label>
                {input(
                  combo.surcharge.kind === "PERCENT" ? "Recargo (%)" : "Importe del recargo",
                  combo.surcharge.amount,
                  (amount) => patchCombo(index, { surcharge: { ...combo.surcharge, amount } }),
                  true,
                )}
                <label>
                  <span>Moneda del recargo</span>
                  <select
                    value={combo.surcharge.currency}
                    onChange={(e) =>
                      patchCombo(index, {
                        surcharge: { ...combo.surcharge, currency: e.target.value },
                      })
                    }
                  >
                    {["CLP", "USD", "UF"].map((c) => (
                      <option key={c} value={c}>
                        {c}
                      </option>
                    ))}
                  </select>
                </label>
                {input("Fuente del recargo", combo.surcharge.source, (source) =>
                  patchCombo(index, { surcharge: { ...combo.surcharge, source } }),
                )}
                {input(
                  "Colores compatibles de manilla (códigos separados por coma)",
                  combo.allowed_handle_colors.join(", "),
                  (v) =>
                    patchCombo(index, {
                      allowed_handle_colors: v
                        .split(",")
                        .map((c) => c.trim())
                        .filter(Boolean),
                    }),
                )}
                {input("Fuente de las restricciones", combo.source, (source) =>
                  patchCombo(index, { source }),
                )}
                {flag("Reglas sintéticas DEMO", combo.synthetic, (synthetic) =>
                  patchCombo(index, { synthetic }),
                )}
              </div>
              <button
                type="button"
                onClick={() =>
                  onChange({
                    ...value,
                    combinations: value.combinations.filter((_, i) => i !== index),
                  })
                }
              >
                Quitar combinación
              </button>
            </details>
          ))}
          <button
            type="button"
            onClick={() =>
              onChange({
                ...value,
                combinations: [
                  ...value.combinations,
                  {
                    code: "",
                    interior: "",
                    exterior: "",
                    base: null,
                    reinforcement_required: false,
                    reinforcement_stock_code: "",
                    glass_clearance_mm: "",
                    max_position_width_mm: null,
                    max_position_height_mm: null,
                    max_leaf_width_mm: null,
                    max_leaf_height_mm: null,
                    extra_lead_days: null,
                    surcharge: { kind: "NONE", amount: "", currency: "CLP", source: "" },
                    allowed_handle_colors: [],
                    source: "",
                    synthetic: false,
                  },
                ],
              })
            }
          >
            Agregar combinación
          </button>
          <button type="button" onClick={() => onChange(null)}>
            Retirar carta de esta revisión
          </button>
        </>
      )}
    </fieldset>
  );
}
