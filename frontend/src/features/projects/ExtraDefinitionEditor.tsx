import { useState } from "react";
import { decimalInputValue } from "../../decimal";
import {
  extraBasisLabels,
  extraImportSummary,
  sideLabels,
  type ExtraAuthority,
  type ExtraDefinition,
} from "./extraModel";
import "./extras.css";

export function emptyExtra(kind: ExtraDefinition["kind"] = "SERVICE"): ExtraDefinition {
  return {
    code: "",
    name: "",
    scope: kind === "SERVICE" ? "PROJECT" : "POSITION",
    kind,
    basis: kind === "PROFILE" ? "SILL" : kind === "SERVICE" ? "PERIMETER" : "WINDOW",
    unit: kind === "PROFILE" || kind === "SERVICE" ? "M" : "EA",
    currency: "CLP",
    cost_rate: "",
    selling_rate: "",
    source: "",
    synthetic: false,
    default_sides: [],
    allowed_movements: [],
    zones: {},
    profile_role: kind === "PROFILE" ? "SILL" : null,
  };
}

export function ExtraDefinitionEditor({
  value,
  onChange,
  servicesOnly = false,
  costsVisible = true,
}: {
  value: ExtraDefinition;
  onChange(value: ExtraDefinition): void;
  servicesOnly?: boolean;
  costsVisible?: boolean;
}): JSX.Element {
  const patch = (changes: Partial<ExtraDefinition>) => onChange({ ...value, ...changes });
  const text = (
    label: string,
    current: string | undefined,
    edit: (v: string) => void,
    decimal = false,
  ) => (
    <label>
      {label}
      <input
        value={decimal ? decimalInputValue(current ?? "") : (current ?? "")}
        placeholder="Sin dato"
        inputMode={decimal ? "decimal" : undefined}
        onChange={(e) => edit(decimal ? e.target.value.replace(",", ".") : e.target.value)}
      />
    </label>
  );
  const bases =
    value.kind === "PROFILE"
      ? ["SILL", "SIDES"]
      : value.kind === "SERVICE"
        ? ["AREA", "PERIMETER", "PER_POSITION", "FIXED", "ZONE"]
        : ["WINDOW", "LEAF"];
  function basis(next: string) {
    patch({
      basis: next as ExtraDefinition["basis"],
      unit: next === "AREA" ? "M2" : ["SILL", "SIDES", "PERIMETER"].includes(next) ? "M" : "EA",
      zones: next === "ZONE" ? (value.zones ?? {}) : {},
      default_sides: next === "SIDES" ? (value.default_sides ?? []) : [],
    });
  }
  return (
    <div className="extra-authority-fields">
      {text("Código del extra", value.code, (code) => patch({ code }))}
      {text("Nombre", value.name, (name) => patch({ name }))}
      {!servicesOnly && (
        <label>
          Tipo
          <select
            value={value.kind}
            onChange={(e) =>
              onChange({
                ...emptyExtra(e.target.value as ExtraDefinition["kind"]),
                code: value.code,
                name: value.name,
                source: value.source,
              })
            }
          >
            <option value="PROFILE">Perfil con cortes</option>
            <option value="SCREEN">Mosquitero a medida</option>
            <option value="FITTING">Accesorio por unidad</option>
            <option value="SERVICE">Servicio</option>
          </select>
        </label>
      )}
      {value.kind === "SERVICE" && (
        <label>
          Aplicar en
          <select
            value={value.scope}
            onChange={(e) => patch({ scope: e.target.value as ExtraDefinition["scope"] })}
          >
            <option value="PROJECT">Proyecto</option>
            <option value="POSITION">Cada posición</option>
          </select>
        </label>
      )}
      <label>
        Cantidad desde el motor
        <select value={value.basis} onChange={(e) => basis(e.target.value)}>
          {bases.map((key) => (
            <option key={key} value={key}>
              {extraBasisLabels[key]}
            </option>
          ))}
        </select>
      </label>
      <label>
        Moneda de la tarifa
        <select
          value={value.currency}
          onChange={(e) => patch({ currency: e.target.value as "CLP" | "USD" })}
        >
          <option>CLP</option>
          <option>USD</option>
        </select>
      </label>
      {value.basis !== "ZONE" && (
        <>
          {costsVisible &&
            text(
              "Costo unitario de suministro completo",
              value.cost_rate,
              (cost_rate) => patch({ cost_rate }),
              true,
            )}
          {text(
            "Tarifa de venta por unidad",
            value.selling_rate,
            (selling_rate) => patch({ selling_rate }),
            true,
          )}
        </>
      )}
      {text("Fuente y condiciones de la tarifa", value.source, (source) => patch({ source }))}
      <label>
        <input
          type="checkbox"
          checked={value.synthetic}
          onChange={(e) => patch({ synthetic: e.target.checked })}
        />
        Autoridad sintética · DEMO
      </label>
      {value.kind === "SERVICE" && (
        <label>
          <input
            type="checkbox"
            checked={value.installation ?? false}
            onChange={(e) => patch({ installation: e.target.checked })}
          />
          Es instalación · reemplaza la tarifa histórica por m²
        </label>
      )}
      {value.kind === "PROFILE" ? (
        <>
          <label>
            Rol del perfil
            <select
              value={value.profile_role ?? ""}
              onChange={(e) => patch({ profile_role: e.target.value })}
            >
              <option value="SILL">Vierteaguas</option>
              <option value="FRAME_EXTENSION">Ensanche</option>
              <option value="COVER_TRIM">Tapajuntas</option>
              <option value="ADDITIONAL">Perfil adicional</option>
            </select>
          </label>
          {value.basis === "SILL" &&
            text(
              "Vuelo predeterminado por extremo · mm",
              value.default_overhang_mm,
              (v) => patch({ default_overhang_mm: v }),
              true,
            )}
          {value.basis === "SIDES" && (
            <fieldset>
              <legend>Lados predeterminados</legend>
              {Object.entries(sideLabels).map(([side, label]) => (
                <label key={side}>
                  <input
                    type="checkbox"
                    checked={(value.default_sides ?? []).includes(side as keyof typeof sideLabels)}
                    onChange={(e) =>
                      patch({
                        default_sides: e.target.checked
                          ? [...(value.default_sides ?? []), side as keyof typeof sideLabels]
                          : (value.default_sides ?? []).filter((v) => v !== side),
                      })
                    }
                  />
                  {label}
                </label>
              ))}
            </fieldset>
          )}
        </>
      ) : (
        value.kind !== "SERVICE" && (
          <>
            {text("Artículo de compra a medida", value.sku ?? "", (sku) => patch({ sku }))}
            <label>
              <input
                type="checkbox"
                checked={value.replaces_handle ?? false}
                onChange={(e) => patch({ replaces_handle: e.target.checked })}
              />
              Reemplaza la manilla base de la hoja
            </label>
          </>
        )
      )}
      {value.kind !== "SERVICE" && (
        <details>
          <summary>Avanzado · compatibilidad y sugerencia</summary>
          <p>Sin aperturas restringidas: compatible con todas las aperturas de la serie.</p>
          {["FIXED", "TURN", "TILT_TURN", "TOP_HUNG", "BOTTOM_HUNG", "SLIDE", "LIFT_SLIDE"].map(
            (key, index) => (
              <label key={key}>
                <input
                  type="checkbox"
                  checked={(value.allowed_movements ?? []).includes(key)}
                  onChange={(e) =>
                    patch({
                      allowed_movements: e.target.checked
                        ? [...(value.allowed_movements ?? []), key]
                        : (value.allowed_movements ?? []).filter((v) => v !== key),
                    })
                  }
                />
                {
                  [
                    "Fijo",
                    "Abatible",
                    "Oscilobatiente",
                    "Proyectante",
                    "Abatimiento inferior",
                    "Corredera",
                    "Elevable corredera",
                  ][index]
                }
              </label>
            ),
          )}
          <label>
            Sugerir cuando
            <select
              value={value.suggestion ?? "NONE"}
              onChange={(e) =>
                patch({ suggestion: e.target.value as ExtraDefinition["suggestion"] })
              }
            >
              <option value="NONE">No sugerir</option>
              <option value="WINDOW">Hay una ventana</option>
              <option value="MOVING_LEAF">Hay una hoja móvil compatible</option>
              <option value="OPENING_GAP">El vano de obra excede el marco</option>
            </select>
          </label>
        </details>
      )}
      {value.basis === "ZONE" && (
        <div className="extra-zones">
          <h4>Tarifas por zona</h4>
          {Object.entries(value.zones ?? {}).map(([zone, rate], index) => (
            <div key={index} className="extra-authority-fields">
              {text("Zona", zone, (name) => {
                const entries = Object.entries(value.zones ?? {});
                entries[index] = [name, rate];
                patch({ zones: Object.fromEntries(entries) });
              })}
              {costsVisible &&
                text(
                  "Costo de la zona",
                  rate.cost_rate,
                  (v) => patch({ zones: { ...value.zones, [zone]: { ...rate, cost_rate: v } } }),
                  true,
                )}
              {text(
                "Venta de la zona",
                rate.selling_rate,
                (v) => patch({ zones: { ...value.zones, [zone]: { ...rate, selling_rate: v } } }),
                true,
              )}
              <button
                type="button"
                onClick={() =>
                  patch({
                    zones: Object.fromEntries(
                      Object.entries(value.zones ?? {}).filter(([name]) => name !== zone),
                    ),
                  })
                }
              >
                Quitar zona
              </button>
            </div>
          ))}
          <button
            type="button"
            onClick={() =>
              patch({
                zones: {
                  ...value.zones,
                  [`Zona ${Object.keys(value.zones ?? {}).length + 1}`]: {
                    cost_rate: "",
                    selling_rate: "",
                  },
                },
                cost_rate: "0",
                selling_rate: "0",
              })
            }
          >
            Agregar zona
          </button>
        </div>
      )}
    </div>
  );
}

export function ExtraImport<T extends { schema_version: 1 }>({
  value,
  onChange,
  parse,
}: {
  value: T;
  onChange(value: T): void;
  parse(value: unknown): T;
}): JSX.Element {
  const [text, setText] = useState("");
  const [proposed, setProposed] = useState<T | null>(null);
  const [error, setError] = useState("");
  return (
    <details className="extra-import">
      <summary>Importar desde una fuente · JSON</summary>
      <p>Las medidas y tarifas se validan al guardar. Revisa la propuesta antes de incorporarla.</p>
      <button
        type="button"
        onClick={() => {
          const blob = new Blob([JSON.stringify(value, null, 2)], { type: "application/json" });
          const url = URL.createObjectURL(blob);
          const link = document.createElement("a");
          link.href = url;
          link.download = "autoridad-extras.json";
          link.click();
          URL.revokeObjectURL(url);
        }}
      >
        Descargar autoridad actual
      </button>
      <label>
        Archivo de autoridad
        <input
          type="file"
          accept=".json,application/json"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) void file.text().then(setText);
            setProposed(null);
          }}
        />
      </label>
      <label>
        Contenido de la fuente
        <textarea
          value={text}
          onChange={(e) => {
            setText(e.target.value);
            setProposed(null);
          }}
        />
      </label>
      <button
        type="button"
        disabled={!text.trim()}
        onClick={() => {
          try {
            setProposed(parse(JSON.parse(text)));
            setError("");
          } catch {
            setError("El archivo no declara una autoridad válida. Revisa su estructura y versión.");
          }
        }}
      >
        Revisar importación
      </button>
      {error && <p role="alert">{error}</p>}
      {proposed && (
        <div>
          <h4>Revisión de cambios</h4>
          <div className="extra-import-diff">
            <section>
              <h5>Actual</h5>
              <ul className="extra-selected extra-equation">
                {extraImportSummary(value).map((line, at) => (
                  <li key={at}>{line}</li>
                ))}
              </ul>
            </section>
            <section>
              <h5>Propuesto</h5>
              <ul className="extra-selected extra-equation">
                {extraImportSummary(proposed).map((line, at) => (
                  <li key={at}>{line}</li>
                ))}
              </ul>
            </section>
          </div>
          <details>
            <summary>Detalles técnicos de la propuesta</summary>
            <h5>Actual</h5>
            <pre>{JSON.stringify(value, null, 2)}</pre>
            <h5>Propuesto</h5>
            <pre>{JSON.stringify(proposed, null, 2)}</pre>
          </details>
          <button
            type="button"
            onClick={() => {
              onChange(proposed);
              setProposed(null);
            }}
          >
            Incorporar propuesta revisada
          </button>
          <button type="button" onClick={() => setProposed(null)}>
            Descartar propuesta
          </button>
        </div>
      )}
    </details>
  );
}

export function ExtraAuthorityEditor({
  value,
  onChange,
  costsVisible = true,
}: {
  value: ExtraAuthority | null;
  onChange(value: ExtraAuthority | null): void;
  costsVisible?: boolean;
}): JSX.Element {
  return (
    <fieldset className="catalog-group">
      <legend>Accesorios y extras con autoridad</legend>
      {!costsVisible && (
        <p>
          Los costos de compra son confidenciales. El dueño o jefe de taller puede consultarlos.
        </p>
      )}
      <p>
        Los perfiles usan cortes, refuerzo y stock del rol declarado. La tarifa debe cubrir su
        suministro completo en los acabados compatibles; documenta sus condiciones.
      </p>
      {!value ? (
        <>
          <p>Sin autoridad de extras para esta versión.</p>
          <button
            type="button"
            onClick={() => onChange({ schema_version: 1, source: "", definitions: [] })}
          >
            Declarar accesorios desde una fuente
          </button>
        </>
      ) : (
        <>
          <label>
            Fuente de la autoridad
            <input
              value={value.source}
              onChange={(e) => onChange({ ...value, source: e.target.value })}
            />
          </label>
          {value.definitions.map((item, index) => (
            <details className="extra-authority-row" key={index}>
              <summary>
                {item.name || "Extra sin nombre"}
                {item.synthetic && " · DEMO"}
              </summary>
              <ExtraDefinitionEditor
                value={item}
                costsVisible={costsVisible}
                onChange={(next) =>
                  onChange({
                    ...value,
                    definitions: value.definitions.map((v, i) => (i === index ? next : v)),
                  })
                }
              />
              <button
                type="button"
                onClick={() =>
                  onChange({
                    ...value,
                    definitions: value.definitions.filter((_, i) => i !== index),
                  })
                }
              >
                Quitar definición
              </button>
            </details>
          ))}
          <button
            type="button"
            onClick={() =>
              onChange({ ...value, definitions: [...value.definitions, emptyExtra("PROFILE")] })
            }
          >
            Agregar definición de extra
          </button>
          <ExtraImport<ExtraAuthority>
            value={value}
            onChange={(next) => onChange(next)}
            parse={(input) => {
              const v = input as ExtraAuthority;
              if (
                v?.schema_version !== 1 ||
                !Array.isArray(v.definitions) ||
                typeof v.source !== "string"
              )
                throw new Error();
              return v;
            }}
          />
        </>
      )}
    </fieldset>
  );
}
