import { useEffect, useRef, useState } from "react";
import { LoadingState } from "../../ui/States";
import { useQuery } from "@tanstack/react-query";
import { hardwarePreview } from "../../api/generated/dekopen";
import { ApiError } from "../../api/apiMutator";
import type { DesignOptions } from "../../api/generated/models";
import { fmtMm, formatMoney, formatDecimal, parseDecimalInput } from "../../format";
import type { IntentNode } from "./intentEditing";
import type { ProductModuleJson } from "./productEditing";
import type {
  HardwareClass,
  HardwareResolution,
  HardwareSelection,
  ResolvedHardwareComponent,
} from "./hardwareContracts";
import "./hardware.css";

function displayRestriction(message: string): string {
  return message
    .replace(
      /(-?\d+(?:[.,]\d+)?)\s+kg\b/g,
      (_, value: string) => `${formatDecimal(value.replace(",", "."), 1)} kg`,
    )
    .replace(/\b\d+\.\d+\b/g, (value) => fmtMm(value));
}

function HeightField({
  value,
  disabled,
  onCommit,
}: {
  value: string;
  disabled: boolean;
  onCommit(value: string): void;
}): JSX.Element {
  const [draft, setDraft] = useState(value);
  const [error, setError] = useState(false);
  function commit(): void {
    const parsed = parseDecimalInput(draft);
    setError(parsed === null);
    if (parsed !== null && parsed !== value) onCommit(parsed);
  }
  return (
    <label className="assembly-field">
      <span>Altura de manilla desde la base (mm)</span>
      <input
        aria-label="Altura de manilla desde la base (mm)"
        inputMode="decimal"
        value={draft}
        disabled={disabled}
        aria-invalid={error}
        onChange={(event) => setDraft(event.target.value)}
        onBlur={commit}
        onKeyDown={(event) => {
          if (event.key === "Enter") {
            event.preventDefault();
            commit();
          }
        }}
      />
      {error && <small role="alert">Ingresa una medida decimal en milímetros.</small>}
    </label>
  );
}

export function HardwarePanel({
  options,
  module,
  bay,
  organizationId,
  color,
  busy,
  onPatch,
  onTree,
}: {
  options?: DesignOptions;
  module: ProductModuleJson;
  bay: IntentNode;
  organizationId: string;
  color: string;
  busy: boolean;
  onPatch(patch: Partial<IntentNode>): void;
  onTree?(tree: IntentNode): void;
}): JSX.Element {
  const [proposal, setProposal] = useState<string | null>(null);
  const panel = useRef<HTMLElement>(null);
  useEffect(() => {
    function explain(event: KeyboardEvent): void {
      if (event.key !== "F6" || !panel.current) return;
      event.preventDefault();
      panel.current.querySelectorAll<HTMLDetailsElement>(".hardware-advanced").forEach((detail) => {
        detail.open = true;
      });
      panel.current.querySelector<HTMLElement>(".hardware-advanced summary")?.focus();
    }
    window.addEventListener("keydown", explain);
    return () => window.removeEventListener("keydown", explain);
  }, []);
  const query = useQuery({
    queryKey: ["hardware-preview", organizationId, options?.system_id, color, module, bay.id],
    queryFn: async () => {
      const response = await hardwarePreview(
        {
          system_id: options!.system_id,
          width_mm: module.width_mm,
          height_mm: module.height_mm,
          color,
          bay_id: bay.id,
          parametric_tree: module.tree,
        },
        { headers: { "X-Organization-ID": organizationId } },
      );
      if (response.status !== 200) throw new Error("hardware_preview_failed");
      return response.data;
    },
    enabled: Boolean(options?.system_id && options.hardware_kits.length),
    retry: false,
    staleTime: Infinity,
  });
  if (!options?.hardware_kits.length)
    return (
      <section className="hardware-panel">
        <h5>Herrajes</h5>
        <p>Sin dato: esta serie no declara herrajes. Completa su catálogo para resolver la hoja.</p>
      </section>
    );
  if (query.isPending)
    return (
      <section className="hardware-panel" aria-busy="true">
        <h5>Herrajes</h5>
        <LoadingState label="Resolviendo clase y componentes" />
      </section>
    );
  if (query.isError)
    return (
      <section className="hardware-panel">
        <h5>Herrajes</h5>
        <p role="alert">
          {query.error instanceof ApiError && query.error.status === 403
            ? "Tu rol no permite consultar esta ingeniería. Solicita acceso a tu organización."
            : "Sin dato: no se pudo resolver la hoja. Revisa medidas, vidrio y fuentes del catálogo."}
        </p>
        <button type="button" disabled={query.isFetching} onClick={() => void query.refetch()}>
          Volver a resolver
        </button>
      </section>
    );
  if (!query.data?.leaves.length)
    return (
      <section className="hardware-panel">
        <h5>Herrajes</h5>
        <p>Esta apertura no tiene hojas móviles que requieran herraje.</p>
      </section>
    );
  return (
    <section ref={panel} className="hardware-panel" aria-label="Herrajes resueltos">
      <h5>Herrajes {query.data.is_demo && <span className="hardware-demo">DEMO</span>}</h5>
      {query.data.division != null &&
        onTree &&
        (() => {
          const division = query.data.division as {
            tree: IntentNode;
            delta_net: string | null;
            price_reason: string | null;
            description: string;
          };
          return (
            <div className="hardware-proposal">
              {proposal !== "division" ? (
                <button type="button" disabled={busy} onClick={() => setProposal("division")}>
                  Revisar división compatible
                </button>
              ) : (
                <>
                  <p>{division.description}</p>
                  <p className="hardware-number">
                    Δ herrajes:{" "}
                    {division.delta_net === null
                      ? "Sin dato de precio comparativo"
                      : `${formatMoney(division.delta_net)} neto`}
                    .
                  </p>
                  {division.price_reason && <p>{division.price_reason}</p>}
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() => {
                      onTree(division.tree);
                      setProposal(null);
                    }}
                  >
                    Aplicar división
                  </button>
                  <button type="button" disabled={busy} onClick={() => setProposal(null)}>
                    Conservar hoja
                  </button>
                </>
              )}
            </div>
          );
        })()}
      {query.data.leaves.map((leaf, ordinal) => {
        const selected = leaf.candidates.find((candidate) => candidate.selected);
        const resolution = selected?.resolution as HardwareResolution | null | undefined;
        const authority = selected?.class_authority as HardwareClass | null | undefined;
        const handle = authority?.handles.find(
          (item) => item.code === (bay.hardware_selection?.handle_code ?? authority.default_handle),
        );
        const proposed = leaf.candidates.find(
          (candidate) => candidate.sku === proposal && candidate.compatible,
        );
        const recommended = leaf.candidates.find(
          (candidate) => candidate.sku === leaf.recommendation_sku && candidate.compatible,
        );
        const selection: HardwareSelection = bay.hardware_selection ?? { option_codes: [] };
        function patchSelection(patch: Partial<HardwareSelection>): void {
          onPatch({ hardware_selection: { ...selection, ...patch } });
        }
        return (
          <div key={leaf.leaf_id ?? ordinal} className="hardware-leaf">
            {query.data!.leaves.length > 1 && <h6>Hoja {ordinal + 1}</h6>}
            <p className="hardware-class">
              <strong>{resolution?.class_name ?? selected?.name ?? "Sin clase compatible"}</strong>
              <span>
                {selected?.compatible
                  ? "Compatible · resuelta por el motor"
                  : "Bloqueada · revisa la restricción"}
              </span>
            </p>
            {leaf.message && (
              <p className="hardware-warning" role="alert">
                {displayRestriction(leaf.message)}
              </p>
            )}
            {recommended && leaf.editable && (
              <button type="button" disabled={busy} onClick={() => setProposal(recommended.sku)}>
                Revisar{" "}
                {(recommended.resolution as HardwareResolution | null)?.class_name ??
                  recommended.name}
                {recommended.delta_net !== null
                  ? ` · Δ ${formatMoney(recommended.delta_net)} neto`
                  : " · Sin dato de precio"}
              </button>
            )}
            {proposed && leaf.editable && (
              <div
                className="hardware-proposal"
                role="region"
                aria-label="Cambio de clase propuesto"
              >
                <p>
                  {resolution?.class_name ?? selected?.name} →{" "}
                  {(proposed.resolution as HardwareResolution | null)?.class_name ?? proposed.name}
                </p>
                <p className="hardware-number">
                  Δ{" "}
                  {proposed.delta_net === null
                    ? "Sin dato: completa costos antes de comparar."
                    : `${formatMoney(proposed.delta_net)} neto por hoja`}
                </p>
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => {
                    onPatch({ hardware_set_sku: proposed.sku });
                    setProposal(null);
                  }}
                >
                  Aplicar clase
                </button>
                <button type="button" disabled={busy} onClick={() => setProposal(null)}>
                  Conservar clase
                </button>
              </div>
            )}
            {handle && leaf.editable && (
              <>
                <label className="assembly-field">
                  <span>Modelo de manilla</span>
                  <select
                    aria-label="Modelo de manilla"
                    disabled={busy}
                    value={handle.code}
                    onChange={(event) => {
                      const next = authority!.handles.find(
                        (item) => item.code === event.target.value,
                      )!;
                      patchSelection({ handle_code: next.code, color_code: next.default_color });
                    }}
                  >
                    {authority!.handles.map((item) => (
                      <option key={item.code} value={item.code}>
                        {item.name}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="assembly-field">
                  <span>Color de manilla</span>
                  <select
                    aria-label="Color de manilla"
                    disabled={busy}
                    value={selection.color_code ?? handle.default_color}
                    onChange={(event) => patchSelection({ color_code: event.target.value })}
                  >
                    {handle.colors.map((item) => (
                      <option key={item.code} value={item.code}>
                        {item.name}
                      </option>
                    ))}
                  </select>
                </label>
                {resolution?.handle_height_mm !== null &&
                  resolution?.handle_height_mm !== undefined && (
                    <>
                      <HeightField
                        key={resolution.handle_height_mm + (bay.handle_height_mm ?? "")}
                        value={bay.handle_height_mm ?? resolution.handle_height_mm}
                        disabled={
                          busy || resolution.handle_minimum_mm === resolution.handle_maximum_mm
                        }
                        onCommit={(value) => onPatch({ handle_height_mm: value })}
                      />
                      <p className="hardware-number">
                        Rango de la fuente: {fmtMm(resolution.handle_minimum_mm)}–
                        {fmtMm(resolution.handle_maximum_mm)} mm.
                      </p>
                    </>
                  )}
              </>
            )}
            {authority && leaf.editable && authority.options.length > 0 && (
              <details>
                <summary>Opciones vendibles</summary>
                <fieldset className="hardware-options">
                  <legend className="visually-hidden">Opciones de esta clase</legend>
                  {authority.options.map((option) => (
                    <label key={option.code}>
                      <input
                        type="checkbox"
                        disabled={busy}
                        checked={selection.option_codes.includes(option.code)}
                        onChange={(event) =>
                          patchSelection({
                            option_codes: event.target.checked
                              ? [...selection.option_codes, option.code]
                              : selection.option_codes.filter((code) => code !== option.code),
                          })
                        }
                      />
                      {option.name}
                      {option.security_rating ? ` · ${option.security_rating}` : ""}
                    </label>
                  ))}
                </fieldset>
              </details>
            )}
            <details className="hardware-advanced">
              <summary>Avanzado · ¿Por qué este kit?</summary>
              <label className="assembly-field">
                <span>Clase de herraje</span>
                <select
                  aria-label="Clase de herraje"
                  disabled={busy || !leaf.editable}
                  value={selected?.sku ?? ""}
                  onChange={(event) => setProposal(event.target.value)}
                >
                  {!selected && <option value="">Sin clase compatible</option>}
                  {leaf.candidates.map((candidate) => (
                    <option
                      key={candidate.sku}
                      value={candidate.sku}
                      disabled={!candidate.compatible}
                    >
                      {(candidate.resolution as HardwareResolution | null)?.class_name ??
                        candidate.name}
                      {candidate.compatible ? "" : " · incompatible"}
                    </option>
                  ))}
                </select>
              </label>
              {resolution && (
                <dl className="hardware-facts">
                  <div>
                    <dt>Hoja terminada</dt>
                    <dd>
                      {fmtMm(resolution.width_mm)} × {fmtMm(resolution.height_mm)} mm
                    </dd>
                  </div>
                  <div>
                    <dt>Peso con herraje</dt>
                    <dd>
                      {resolution.exact_leaf_weight_kg === null
                        ? "Sin dato"
                        : `${formatDecimal(resolution.exact_leaf_weight_kg, 1)} kg`}
                    </dd>
                  </div>
                  <div>
                    <dt>Capacidad de clase</dt>
                    <dd>{fmtMm(resolution.max_leaf_weight_kg)} kg</dd>
                  </div>
                  <div>
                    <dt>Ancho admitido</dt>
                    <dd>
                      {fmtMm(resolution.min_leaf_width_mm)}–{fmtMm(resolution.max_leaf_width_mm)} mm
                    </dd>
                  </div>
                  <div>
                    <dt>Alto admitido</dt>
                    <dd>
                      {fmtMm(resolution.min_leaf_height_mm)}–{fmtMm(resolution.max_leaf_height_mm)}{" "}
                      mm
                    </dd>
                  </div>
                </dl>
              )}
              <p className="hardware-source">
                Fuente:{" "}
                {resolution?.source ??
                  "Contenido histórico declarado en el catálogo de esta serie."}
              </p>
              {resolution && (
                <details>
                  <summary>Detalles técnicos de la clase</summary>
                  <p>
                    Peso exacto usado al validar:{" "}
                    <code>{resolution.exact_leaf_weight_kg ?? "Sin dato"}</code> kg.
                  </p>
                </details>
              )}
              <ul className="hardware-components">
                {((selected?.contents as ResolvedHardwareComponent[] | undefined) ?? []).map(
                  (component, index) => (
                    <li key={component.sku + index}>
                      <div>
                        <span>{component.name}</span>
                        <span className="hardware-number">
                          {fmtMm(component.qty)} un.
                          {component.cut_length_mm != null
                            ? ` · ${fmtMm(component.cut_length_mm)} mm`
                            : ""}
                        </span>
                      </div>
                      <details>
                        <summary>Regla y fuente</summary>
                        <p>{component.reason ?? "Cantidad fija declarada por el catálogo."}</p>
                        <p>
                          {component.source ??
                            "Sin dato: solicita la fuente técnica del componente."}
                        </p>
                        {component.machining?.map((declaration, index) => (
                          <p key={index}>
                            {declaration.name} ·{" "}
                            {declaration.positions_mm.length
                              ? "Coordenadas declaradas; fabricación verifica cobertura, pieza, cara, herramienta y profundidad."
                              : "Declarada no emitida: faltan coordenadas de catálogo."}
                          </p>
                        ))}
                        <details>
                          <summary>Detalles técnicos</summary>
                          <code>{component.sku}</code>
                        </details>
                      </details>
                    </li>
                  ),
                )}
              </ul>
              <p className="hardware-number">
                Herrajes por hoja:{" "}
                {selected?.price_net != null ? formatMoney(selected.price_net) : "Sin dato"} neto.
              </p>
              {selected?.price_reason && <p>{selected.price_reason}</p>}
              <p className="hardware-source">{query.data!.pricing_basis}</p>
            </details>
          </div>
        );
      })}
    </section>
  );
}
