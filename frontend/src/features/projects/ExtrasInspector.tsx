import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { positionExtrasPreview } from "../../api/generated/dekopen";
import type { DesignOptions, EngineAssemblyCalculateResponse } from "../../api/generated/models";
import { ApiError } from "../../api/apiMutator";
import { actionErrorDetail } from "../errors";
import { useAuthSession } from "../../auth/AuthSessionProvider";
import { fmtMm, formatMoney } from "../../format";
import { decimalInputValue, parseDecimalInput } from "../../decimal";
import { useCanvasStore } from "../canvas/canvasStore";
import { setModuleTree, type ProductJson, type ProductModuleJson } from "../canvas/productEditing";
import {
  definitions,
  extraLines,
  extraBasisLabels,
  extraUnit,
  extraQuantity,
  extraTariff,
  hasRounding,
  sideLabels,
  type ExtraSelection,
  type ExtraSuggestion,
} from "./extraModel";
import "./extras.css";

function Measure({
  label,
  value,
  onValue,
  disabled,
  optional = false,
}: {
  label: string;
  value: string;
  onValue(value: string): void;
  disabled: boolean;
  optional?: boolean;
}) {
  const [draft, setDraft] = useState(decimalInputValue(value));
  const [error, setError] = useState(false);
  useEffect(() => setDraft(decimalInputValue(value)), [value]);
  return (
    <label className="extra-measure">
      {label}
      <input
        inputMode="decimal"
        value={draft}
        disabled={disabled}
        aria-invalid={error}
        onChange={(event) => {
          setDraft(event.target.value);
          setError(false);
        }}
        onBlur={() => {
          if (optional && draft.trim() === "") {
            onValue("");
            return;
          }
          const parsed = parseDecimalInput(draft);
          if (
            parsed === null ||
            parsed.startsWith("-") ||
            (optional && /^0(?:\.0*)?$/.test(parsed))
          ) {
            setError(true);
            return;
          }
          onValue(parsed);
        }}
      />
      {error && (
        <small role="alert">Indica milímetros positivos o cero, con hasta dos decimales.</small>
      )}
    </label>
  );
}

export function ExtrasInspector({
  options,
  module,
  product,
  evaluation,
  busy,
  commit,
}: {
  options?: DesignOptions;
  module: ProductModuleJson;
  product: ProductJson;
  evaluation: EngineAssemblyCalculateResponse | null;
  busy: boolean;
  commit(product: ProductJson): void;
}): JSX.Element {
  const org = useAuthSession().me?.active_organization;
  const inputs = useCanvasStore((state) => state.inputs);
  const choices = definitions(options?.extra_definitions);
  const selections = module.tree.extras ?? [];
  const [picked, setPicked] = useState("");
  const preview = useQuery({
    queryKey: ["position-extras", org?.id, inputs.systemId, inputs.color, module],
    enabled: Boolean(
      org && inputs.systemId && choices.length && !module.frameless && !module.contour,
    ),
    queryFn: async () => {
      const result = await positionExtrasPreview(
        {
          system_id: inputs.systemId!,
          color: inputs.color,
          nominal_width_mm: module.width_mm,
          nominal_height_mm: module.height_mm,
          parametric_tree: module.tree,
        },
        { headers: { "X-Organization-ID": org!.id } },
      );
      if (result.status !== 200) throw new ApiError(result.status, result.data);
      return result.data;
    },
  });
  const lines = extraLines(preview.data?.extras);
  const suggestions = (preview.data?.suggestions ?? []) as ExtraSuggestion[];
  const available = choices.filter(
    (item) =>
      preview.data?.available_codes.includes(item.code) &&
      !selections.some((selection) => selection.code === item.code),
  );
  function replace(next: ExtraSelection[]) {
    commit(setModuleTree(product, module.id, { ...module.tree, extras: next }));
  }
  function add(selection: ExtraSelection) {
    replace([...selections.filter((item) => item.code !== selection.code), selection]);
    setPicked("");
  }
  function patch(index: number, value: Partial<ExtraSelection>) {
    replace(selections.map((item, at) => (at === index ? { ...item, ...value } : item)));
  }
  const leafFacts = (preview.data?.leaf_targets ??
    evaluation?.modules.find((item) => item.module_id === module.id)?.result?.opening_leaves ??
    []) as { bay_id: string; leaf_id: string | null; width_mm: string; height_mm: string }[];
  return (
    <details className="inspector-section extra-inspector" open>
      <summary>Extras de la posición</summary>
      {module.contour || module.frameless ? (
        <p className="inspector-note">
          Sin autoridad de accesorios para esta forma. Revisa el catálogo de la serie.
        </p>
      ) : choices.length === 0 ? (
        <p className="inspector-note">
          Sin dato: esta versión no declara extras. Elige una serie con accesorios o completa su
          catálogo.
        </p>
      ) : (
        <>
          {preview.isFetching && <p role="status">Calculando cantidades y precio…</p>}
          {preview.isError && (
            <p role="alert">
              {actionErrorDetail(
                preview.error,
                "No pudimos calcular los extras. Revisa el diseño y vuelve a intentar.",
              )}
              <button type="button" onClick={() => void preview.refetch()}>
                Reintentar
              </button>
            </p>
          )}
          {preview.data?.reason && <p role="alert">Sin dato: {preview.data.reason}</p>}
          {!selections.length && <p className="inspector-note">Todavía no has agregado extras.</p>}
          <p className="inspector-note">
            El palillaje y sus cruces se declaran en Vidrio · Tratamientos, con la tarifa de su
            receta.
          </p>
          {suggestions.map((item) => (
            <div className="extra-proposal" key={item.selection.code}>
              <strong>{item.name}</strong>
              <p>{item.cause}</p>
              <div className="inspector-actions">
                <button
                  type="button"
                  disabled={busy || preview.isFetching}
                  onClick={() => add(item.selection)}
                >
                  Aceptar
                </button>
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => add({ ...item.selection, decision: "DISMISS" })}
                >
                  Descartar
                </button>
              </div>
            </div>
          ))}
          <ul className="extra-selected">
            {selections.map((selection, index) => {
              const definition = choices.find((item) => item.code === selection.code);
              const selectedLines = lines.filter((item) => item.code === selection.code);
              const requiredByMounting =
                inputs.mounting
                  ?.find((item) => item.survey.module_id === module.id)
                  ?.rule.extras.some((item) => item.code === selection.code) ?? false;
              const selectionLocked = busy || requiredByMounting;
              return (
                <li key={`${selection.code}-${index}`}>
                  <header>
                    <strong>{definition?.name ?? "Extra sin autoridad"}</strong>
                    <button
                      type="button"
                      disabled={selectionLocked}
                      onClick={() => replace(selections.filter((_, at) => at !== index))}
                    >
                      Quitar
                    </button>
                  </header>
                  {requiredByMounting && (
                    <p>Exigido por montaje. Para cambiarlo, revisa Vano y montaje.</p>
                  )}
                  {selection.decision === "DISMISS" ? (
                    <p>
                      Descartado.{" "}
                      <button
                        type="button"
                        disabled={selectionLocked}
                        onClick={() => patch(index, { decision: "ACCEPT" })}
                      >
                        Aceptar
                      </button>
                    </p>
                  ) : (
                    <>
                      {definition?.basis === "SILL" && (
                        <div className="extra-measures">
                          <Measure
                            label="Vuelo izquierdo · mm"
                            value={selection.overhang_left_mm ?? "0"}
                            disabled={selectionLocked}
                            onValue={(value) => patch(index, { overhang_left_mm: value })}
                          />
                          <Measure
                            label="Vuelo derecho · mm"
                            value={selection.overhang_right_mm ?? "0"}
                            disabled={selectionLocked}
                            onValue={(value) => patch(index, { overhang_right_mm: value })}
                          />
                        </div>
                      )}
                      {definition?.basis === "SIDES" && (
                        <fieldset className="extra-sides">
                          <legend>Lados</legend>
                          {Object.entries(sideLabels).map(([side, label]) => (
                            <label key={side}>
                              <input
                                type="checkbox"
                                disabled={selectionLocked}
                                checked={(
                                  selection.sides ??
                                  definition.default_sides ??
                                  []
                                ).includes(side as keyof typeof sideLabels)}
                                onChange={(event) => {
                                  const sides = (
                                    selection.sides ??
                                    definition.default_sides ??
                                    []
                                  ).filter((item) => item !== side);
                                  patch(index, {
                                    sides: event.target.checked
                                      ? [...sides, side as keyof typeof sideLabels]
                                      : sides,
                                  });
                                }}
                              />
                              {label}
                            </label>
                          ))}
                        </fieldset>
                      )}
                      {definition?.basis === "LEAF" && leafFacts.length > 1 && (
                        <label>
                          Aplicar a
                          <select
                            disabled={selectionLocked}
                            value={
                              selection.bay_id
                                ? `${selection.bay_id}|${selection.leaf_id ?? ""}`
                                : ""
                            }
                            onChange={(event) => {
                              const leaf = leafFacts.find(
                                (item) =>
                                  `${item.bay_id}|${item.leaf_id ?? ""}` === event.target.value,
                              );
                              patch(index, {
                                bay_id: leaf?.bay_id ?? null,
                                leaf_id: leaf?.leaf_id ?? null,
                              });
                            }}
                          >
                            <option value="">Todas las hojas compatibles</option>
                            {leafFacts.map((leaf, at) => (
                              <option key={at} value={`${leaf.bay_id}|${leaf.leaf_id ?? ""}`}>
                                Hoja {at + 1} · {fmtMm(leaf.width_mm)} × {fmtMm(leaf.height_mm)} mm
                              </option>
                            ))}
                          </select>
                        </label>
                      )}
                      {selectedLines.map((item, at) => (
                        <p className="extra-equation" key={at}>
                          {extraQuantity(item.quantity)} {extraUnit(item.unit)} ×{" "}
                          {extraTariff(
                            item.unit_price ?? item.selling_rate,
                            preview.data?.currency,
                          )}{" "}
                          = <strong>{formatMoney(item.amount, preview.data?.currency)}</strong>
                          {hasRounding(item.rounding) && (
                            <small>
                              Ajuste incluido: {extraQuantity(item.rounding!)}{" "}
                              {preview.data?.currency}
                            </small>
                          )}
                          {item.width_mm && item.height_mm && (
                            <small>
                              {fmtMm(item.width_mm)} × {fmtMm(item.height_mm)} mm
                            </small>
                          )}
                        </p>
                      ))}
                    </>
                  )}
                  <details>
                    <summary>Regla y fuente</summary>
                    <p>
                      {extraBasisLabels[definition?.basis ?? ""] ?? "Sin dato"} ·{" "}
                      {definition?.source ?? "Completa el catálogo"}
                      {definition?.synthetic && " · DEMO"}
                    </p>
                  </details>
                </li>
              );
            })}
          </ul>
          <div className="extra-picker">
            <select
              aria-label="Extra compatible"
              value={picked}
              disabled={busy || preview.isFetching}
              onChange={(event) => setPicked(event.target.value)}
            >
              <option value="">Elige un extra compatible</option>
              {available.map((item) => (
                <option value={item.code} key={item.code}>
                  {item.name}
                  {item.synthetic ? " · DEMO" : ""}
                </option>
              ))}
            </select>
            <button
              type="button"
              disabled={!picked || busy || preview.isFetching}
              onClick={() => {
                const item = choices.find((item) => item.code === picked);
                if (item)
                  add({
                    code: item.code,
                    sides: item.default_sides ?? [],
                    overhang_left_mm: item.basis === "SILL" ? item.default_overhang_mm : "0",
                    overhang_right_mm: item.basis === "SILL" ? item.default_overhang_mm : "0",
                  });
              }}
            >
              Agregar
            </button>
          </div>
          <details>
            <summary>Avanzado · vano de obra</summary>
            <p>Declara las medidas disponibles para que el motor sugiera ensanches con su causa.</p>
            <Measure
              optional
              label="Ancho del vano · mm"
              value={module.tree.extra_context?.opening_width_mm ?? ""}
              disabled={busy}
              onValue={(value) =>
                commit(
                  setModuleTree(product, module.id, {
                    ...module.tree,
                    extra_context: {
                      ...module.tree.extra_context,
                      opening_width_mm: value || undefined,
                    },
                  }),
                )
              }
            />
            <Measure
              optional
              label="Alto del vano · mm"
              value={module.tree.extra_context?.opening_height_mm ?? ""}
              disabled={busy}
              onValue={(value) =>
                commit(
                  setModuleTree(product, module.id, {
                    ...module.tree,
                    extra_context: {
                      ...module.tree.extra_context,
                      opening_height_mm: value || undefined,
                    },
                  }),
                )
              }
            />
          </details>
        </>
      )}
    </details>
  );
}
