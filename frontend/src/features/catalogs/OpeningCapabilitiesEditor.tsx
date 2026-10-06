import type { KitResponse } from "../../api/generated/models";
import { domainLabel } from "../../i18n/domainLabels";
import { decimalInputValue } from "../../decimal";
import type { Capability } from "../canvas/physicalOpenings";

export type PairedRule = {
  meeting_overlap_mm: string;
  meeting_gap_mm: string;
  inversor_end_deduction_mm: string;
  source: string;
};

/** Presence validation only: geometry and permissible ranges remain engine authority. */
export function openingAuthorityProblem(
  capabilities: Capability[],
  paired: PairedRule | null,
): string | null {
  for (const [index, cap] of capabilities.entries()) {
    const name = `Capacidad ${index + 1}`;
    if (!cap.source.trim()) return `${name}: falta la fuente del fabricante.`;
    if (!cap.hinge_sides.length) return `${name}: elige al menos un lado de bisagras.`;
    if (cap.movement !== "FIXED" && !cap.hardware_kit_skus.length)
      return `${name}: elige los herrajes compatibles de la fuente.`;
    if (["ACTIVE", "PASSIVE"].includes(cap.leaf_role) && !paired)
      return `${name}: declara el encuentro con inversor y su fuente.`;
    if (cap.movement !== "FIXED" && cap.movement !== "SLIDE" && cap.leaf_role !== "PASSIVE") {
      const rule = cap.handle_rule;
      if (!rule || !rule.source.trim()) return `${name}: declara la regla de manilla y su fuente.`;
      if (
        !rule.minimum_from_top_mm.trim() ||
        !rule.minimum_from_bottom_mm.trim() ||
        !rule.closing_edge_offset_mm.trim() ||
        (rule.vertical_reference !== "CENTER" && !rule.default_height_mm?.trim())
      )
        return `${name}: completa las medidas de la regla de manilla desde su fuente.`;
    }
  }
  if (
    paired &&
    (!paired.source.trim() ||
      !paired.meeting_overlap_mm.trim() ||
      !paired.meeting_gap_mm.trim() ||
      !paired.inversor_end_deduction_mm.trim())
  )
    return "Encuentro con inversor: completa las medidas y su fuente.";
  return null;
}

/** Catalog authority is entered from a source; empty numeric fields stay empty. */
export function OpeningCapabilitiesEditor({
  capabilities,
  paired,
  kits,
  family,
  onChange,
  onPair,
}: {
  capabilities: Capability[];
  paired: PairedRule | null;
  kits: Pick<KitResponse, "id" | "sku" | "name">[];
  family: string;
  onChange(value: Capability[]): void;
  onPair(value: PairedRule | null): void;
}): JSX.Element {
  const movements =
    family === "FACADE_FIXED"
      ? ["FIXED"]
      : family === "DOOR"
        ? ["FIXED", "TURN"]
        : family === "SLIDING"
          ? ["FIXED", "SLIDE"]
          : ["FIXED", "TURN", "TILT", "TILT_TURN", "TOP_HUNG"];
  function patch(index: number, values: Partial<Capability>): void {
    onChange(capabilities.map((cap, i) => (i === index ? { ...cap, ...values } : cap)));
  }
  function changeMovement(index: number, movement: Capability["movement"]): void {
    patch(index, {
      movement,
      hinge_sides:
        movement === "FIXED" || movement === "SLIDE"
          ? ["NONE"]
          : movement === "TILT"
            ? ["BOTTOM"]
            : movement === "TOP_HUNG"
              ? ["TOP"]
              : ["LEFT", "RIGHT"],
      direction: movement === "TOP_HUNG" ? "OUTWARD" : "INWARD",
      leaf_role: "SINGLE",
      fixed_in_sash: false,
      hardware_kit_skus: [],
      handle_rule: null,
    });
  }
  function handle(index: number, values: Partial<NonNullable<Capability["handle_rule"]>>): void {
    const rule = capabilities[index]?.handle_rule;
    if (rule) patch(index, { handle_rule: { ...rule, ...values } });
  }
  const input = (
    label: string,
    value: string,
    onEdit: (value: string) => void,
    numeric = false,
  ) => (
    <label>
      <span>{label}</span>
      <input
        value={numeric ? decimalInputValue(value) : value}
        title={value}
        inputMode={numeric ? "decimal" : undefined}
        onChange={(event) =>
          onEdit(numeric ? event.target.value.replace(",", ".") : event.target.value)
        }
      />
    </label>
  );
  return (
    <fieldset className="catalog-group">
      <legend>Capacidades de apertura</legend>
      <p>
        Declara cada combinación que la fuente del sistema admite. Una capacidad sin fuente o sin
        herrajes compatibles impide guardar.
      </p>
      {capabilities.length === 0 && (
        <p>Sin dato: agrega una capacidad respaldada por el catálogo del fabricante.</p>
      )}
      {capabilities.map((cap, index) => (
        <fieldset className="catalog-group" key={index}>
          <legend>Capacidad {index + 1}</legend>
          {!cap.source.trim() && (
            <p role="status">
              Bloqueado: falta la fuente de esta capacidad. Completa «Fuente de la capacidad» antes
              de guardar.
            </p>
          )}
          {cap.movement !== "FIXED" && cap.hardware_kit_skus.length === 0 && (
            <p role="status">
              Bloqueado: falta el herraje de esta apertura. Elige un kit respaldado por la fuente.
            </p>
          )}
          <div className="catalog-fields">
            <label>
              <span>Movimiento</span>
              <select
                value={cap.movement}
                onChange={(event) =>
                  changeMovement(index, event.target.value as Capability["movement"])
                }
              >
                {movements.map((value) => (
                  <option key={value} value={value}>
                    {domainLabel(value)}
                  </option>
                ))}
              </select>
            </label>
            <label>
              <span>Dirección</span>
              <select
                value={cap.direction}
                onChange={(event) =>
                  patch(index, { direction: event.target.value as Capability["direction"] })
                }
              >
                <option value="INWARD">Hacia adentro</option>
                <option value="OUTWARD">Hacia afuera</option>
              </select>
            </label>
            <label>
              <span>Rol de la hoja</span>
              <select
                value={cap.leaf_role}
                onChange={(event) =>
                  patch(index, {
                    leaf_role: event.target.value as Capability["leaf_role"],
                    handle_rule: event.target.value === "PASSIVE" ? null : cap.handle_rule,
                  })
                }
              >
                <option value="SINGLE">Hoja única</option>
                <option value="ACTIVE">Activa</option>
                <option value="PASSIVE">Pasiva con falleba</option>
              </select>
            </label>
            {input("Fuente de la capacidad", cap.source, (source) => patch(index, { source }))}
            {cap.movement === "FIXED" && (
              <label>
                <input
                  type="checkbox"
                  checked={cap.fixed_in_sash}
                  onChange={(event) => patch(index, { fixed_in_sash: event.target.checked })}
                />
                Fijo en hoja
              </label>
            )}
          </div>
          {["TURN", "TILT_TURN"].includes(cap.movement) && (
            <div role="group" aria-label={`Bisagras de capacidad ${index + 1}`}>
              {(["LEFT", "RIGHT"] as const).map((side) => (
                <label key={side}>
                  <input
                    type="checkbox"
                    checked={cap.hinge_sides.includes(side)}
                    onChange={(event) =>
                      patch(index, {
                        hinge_sides: event.target.checked
                          ? [...cap.hinge_sides, side]
                          : cap.hinge_sides.filter((value) => value !== side),
                      })
                    }
                  />
                  {side === "LEFT" ? "Bisagras a la izquierda" : "Bisagras a la derecha"}
                </label>
              ))}
            </div>
          )}
          {cap.movement !== "FIXED" && (
            <fieldset className="catalog-group">
              <legend>Herrajes que respaldan la capacidad</legend>
              {kits.length === 0 && <p>Sin dato: registra primero los herrajes de este sistema.</p>}
              {kits.map((kit) => (
                <label key={kit.id}>
                  <input
                    type="checkbox"
                    checked={cap.hardware_kit_skus.includes(kit.sku)}
                    onChange={(event) =>
                      patch(index, {
                        hardware_kit_skus: event.target.checked
                          ? [...cap.hardware_kit_skus, kit.sku]
                          : cap.hardware_kit_skus.filter((value) => value !== kit.sku),
                      })
                    }
                  />
                  {kit.name}
                </label>
              ))}
            </fieldset>
          )}
          {cap.movement !== "FIXED" && cap.movement !== "SLIDE" && cap.leaf_role !== "PASSIVE" && (
            <>
              <label>
                <input
                  type="checkbox"
                  checked={cap.handle_rule !== null}
                  onChange={(event) =>
                    patch(index, {
                      handle_rule: event.target.checked
                        ? {
                            vertical_reference: "CENTER",
                            default_height_mm: null,
                            minimum_from_top_mm: "",
                            minimum_from_bottom_mm: "",
                            closing_edge_offset_mm: "",
                            source: "",
                          }
                        : null,
                    })
                  }
                />
                Declarar regla de manilla
              </label>
              {cap.handle_rule && (
                <div className="catalog-fields">
                  <label>
                    <span>Referencia de altura</span>
                    <select
                      value={cap.handle_rule.vertical_reference}
                      onChange={(event) =>
                        handle(index, {
                          vertical_reference: event.target.value,
                          default_height_mm: event.target.value === "CENTER" ? null : "",
                        })
                      }
                    >
                      <option value="CENTER">Centro de la hoja</option>
                      <option value="LEAF_BOTTOM">Borde inferior de la hoja</option>
                      <option value="LEAF_TOP">Borde superior de la hoja</option>
                    </select>
                  </label>
                  {cap.handle_rule.vertical_reference !== "CENTER" &&
                    input(
                      "Altura de fuente · mm",
                      cap.handle_rule.default_height_mm ?? "",
                      (value) => handle(index, { default_height_mm: value }),
                      true,
                    )}
                  {input(
                    "Margen superior · mm",
                    cap.handle_rule.minimum_from_top_mm,
                    (value) => handle(index, { minimum_from_top_mm: value }),
                    true,
                  )}
                  {input(
                    "Margen inferior · mm",
                    cap.handle_rule.minimum_from_bottom_mm,
                    (value) => handle(index, { minimum_from_bottom_mm: value }),
                    true,
                  )}
                  {input(
                    "Distancia al borde de cierre · mm",
                    cap.handle_rule.closing_edge_offset_mm,
                    (value) => handle(index, { closing_edge_offset_mm: value }),
                    true,
                  )}
                  {input("Fuente de manilla", cap.handle_rule.source, (value) =>
                    handle(index, { source: value }),
                  )}
                </div>
              )}
            </>
          )}
          <button
            type="button"
            onClick={() => onChange(capabilities.filter((_, i) => i !== index))}
          >
            Quitar capacidad {index + 1}
          </button>
        </fieldset>
      ))}
      <button
        type="button"
        onClick={() =>
          onChange([
            ...capabilities,
            {
              use: family === "DOOR" ? "DOOR" : "WINDOW",
              movement: "FIXED",
              direction: "INWARD",
              leaf_role: "SINGLE",
              fixed_in_sash: false,
              hinge_sides: ["NONE"],
              hardware_kit_skus: [],
              handle_rule: null,
              source: "",
            },
          ])
        }
      >
        Agregar capacidad
      </button>
      <label>
        <input
          type="checkbox"
          checked={paired !== null}
          onChange={(event) =>
            onPair(
              event.target.checked
                ? {
                    meeting_overlap_mm: "",
                    meeting_gap_mm: "",
                    inversor_end_deduction_mm: "",
                    source: "",
                  }
                : null,
            )
          }
        />
        Declarar encuentro con inversor
      </label>
      {paired && (
        <div className="catalog-fields">
          {input(
            "Traslape del encuentro · mm",
            paired.meeting_overlap_mm,
            (value) => onPair({ ...paired, meeting_overlap_mm: value }),
            true,
          )}
          {input(
            "Separación del encuentro · mm",
            paired.meeting_gap_mm,
            (value) => onPair({ ...paired, meeting_gap_mm: value }),
            true,
          )}
          {input(
            "Descuento de extremos del inversor · mm",
            paired.inversor_end_deduction_mm,
            (value) => onPair({ ...paired, inversor_end_deduction_mm: value }),
            true,
          )}
          {input("Fuente del encuentro", paired.source, (value) =>
            onPair({ ...paired, source: value }),
          )}
        </div>
      )}
    </fieldset>
  );
}
