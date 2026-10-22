import { useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import {
  catalogSeriesEditCells,
  catalogSeriesSheet,
  catalogSeriesTrial,
  catalogSeriesTrialProposals,
  catalogSeriesTrialVerify,
  projectDesignOptions,
} from "../../api/generated/dekopen";
import type {
  ReferenceWindow,
  SeriesSheet,
  TrialInputRequest,
  TrialMeasurement,
  TrialProposals,
  TrialResponse,
} from "../../api/generated/models";
import { ApiError } from "../../api/apiMutator";
import { compareDecimal, parseDecimalInput } from "../../decimal";
import { fmtMm, formatDateTime } from "../../format";
import { domainLabel } from "../../i18n/domainLabels";
import { Button, Loading } from "../../ui";
import { OpeningSymbol } from "../../ui/OpeningSymbol";
import { legacySymbolOpening } from "../../ui/openingSymbols";
import { TrialMeasurements, trialPiece } from "./TrialMeasurements";
import "./series-trial.css";

function detail(error: unknown): string {
  if (error instanceof ApiError) {
    const payload = error.payload as { error?: { detail?: string } };
    if (payload?.error?.detail) return payload.error.detail;
  }
  return "No se pudo completar la prueba. Conservamos tus medidas; vuelve a intentarlo.";
}

export function SeriesTrial({
  orgId,
  sheet,
  initial,
  onSaved,
  onDraft,
  onBusyChange,
  onVerified,
  onComplete,
}: {
  orgId: string;
  sheet: SeriesSheet;
  initial?: TrialInputRequest;
  onSaved: (sheet: SeriesSheet) => void;
  onDraft?: (draft: TrialInputRequest) => void;
  onBusyChange?: (busy: boolean) => void;
  onVerified?: (reference: ReferenceWindow) => void;
  onComplete: () => void;
}): JSX.Element {
  const tree = initial?.parametric_tree as
    { opening_type?: string; glass_article_sku?: string } | undefined;
  const [width, setWidth] = useState(initial?.nominal_width_mm ?? "1200");
  const [height, setHeight] = useState(initial?.nominal_height_mm ?? "1100");
  const [opening, setOpening] = useState(tree?.opening_type ?? "");
  const [glassSku, setGlassSku] = useState(tree?.glass_article_sku ?? "");
  const [color, setColor] = useState(initial?.color ?? "");
  const [manual, setManual] = useState<Record<string, string>>(initial?.manual_values ?? {});
  const [result, setResult] = useState<TrialResponse | null>(null);
  const [lastInput, setLastInput] = useState<TrialInputRequest | null>(null);
  const [choices, setChoices] = useState<TrialProposals | null>(null);
  const [choice, setChoice] = useState(0);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [confirmed, setConfirmed] = useState(false);
  const [suggested, setSuggested] = useState(false);
  const [receipt, setReceipt] = useState<ReferenceWindow | null>(null);
  const lock = useRef(false);
  const options = { headers: { "X-Organization-ID": orgId } };
  const catalog = useQuery({
    queryKey: ["series-trial-options", orgId, sheet.id, sheet.revision],
    queryFn: async ({ signal }) => {
      const response = await projectDesignOptions(sheet.id, { ...options, signal });
      if (response.status !== 200) throw new Error("options");
      return response.data;
    },
  });
  const glasses =
    catalog.data?.glass_specs.filter(
      (item) => item.compatible !== false && item.spec && item.total_thickness_mm,
    ) ?? [];
  const openings = catalog.data?.compatible_openings ?? [];
  const selectedOpening =
    opening || (openings.includes("TURN_LEFT") ? "TURN_LEFT" : (openings[0] ?? ""));
  const selectedGlass = glasses.find((item) => item.sku === (glassSku || glasses[0]?.sku));
  const selectedColor = color || catalog.data?.colors[0] || "";
  const suggestedCount = sheet.cells.filter((item) => item.origin === "SUGGESTED").length;

  function input(): TrialInputRequest | null {
    const w = parseDecimalInput(width, 2),
      h = parseDecimalInput(height, 2);
    if (
      !w ||
      !h ||
      compareDecimal(w, "0") <= 0 ||
      compareDecimal(h, "0") <= 0 ||
      !selectedGlass ||
      !selectedOpening
    )
      return null;
    const values: Record<string, string> = {};
    for (const [key, raw] of Object.entries(manual)) {
      if (!raw.trim()) continue;
      const value = parseDecimalInput(raw, 2);
      if (!value || compareDecimal(value, "0") <= 0) return null;
      values[key] = value;
    }
    return {
      nominal_width_mm: w,
      nominal_height_mm: h,
      color: selectedColor,
      parametric_tree: {
        id: "trial",
        type: "BAY",
        opening_type: selectedOpening,
        glass_spec: selectedGlass.spec,
        glass_article_sku: selectedGlass.sku,
        glass_thickness_mm: selectedGlass.total_thickness_mm,
      },
      manual_values: values,
    };
  }
  const currentInput = input();
  const changed = JSON.stringify(currentInput) !== JSON.stringify(lastInput);
  const differences = result?.measurements.some((row) => row.matches === false) ?? false;
  const proposal = choices?.items[choice];
  function invalidate() {
    setConfirmed(false);
    setReceipt(null);
    setChoices(null);
  }
  async function run(action: () => Promise<void>) {
    if (lock.current) return;
    lock.current = true;
    setBusy(true);
    onBusyChange?.(true);
    setError("");
    try {
      await action();
    } catch (error) {
      setError(detail(error));
    } finally {
      lock.current = false;
      setBusy(false);
      onBusyChange?.(false);
    }
  }
  async function calculate(data: TrialInputRequest) {
    setLastInput(null);
    setConfirmed(false);
    setChoices(null);
    const response = await catalogSeriesTrial(sheet.id, data, options);
    if (response.status !== 200) throw new Error("trial");
    setResult(response.data);
    setLastInput(data);
    setConfirmed(false);
    setReceipt(null);
    onDraft?.(data);
  }
  function compare() {
    if (!currentInput) {
      setError("Escribe medidas mayores que cero, con hasta dos decimales.");
      return;
    }
    void run(() => calculate(currentInput));
  }
  function propose(row: TrialMeasurement) {
    const target = parseDecimalInput(manual[row.key] ?? "", 2);
    if (!currentInput || !target || compareDecimal(target, "0") <= 0) {
      setError("Completa la medida del manual antes de ajustar la regla.");
      return;
    }
    void run(async () => {
      const response = await catalogSeriesTrialProposals(
        sheet.id,
        { ...currentInput, measurement_key: row.key, target_mm: target },
        options,
      );
      if (response.status !== 200) throw new Error("proposal");
      setChoices(response.data);
      setChoice(0);
    });
  }
  async function apply() {
    if (!proposal || !choices || !currentInput) return;
    const response = await catalogSeriesEditCells(
      sheet.id,
      { revision: choices.revision, changes: [proposal.change] },
      options,
    );
    if (response.status !== 200) throw new Error("apply");
    onSaved(response.data);
    setChoices(null);
    await calculate(currentInput);
  }
  async function verify() {
    if (!result?.measurements.length || !lastInput || !confirmed || changed || differences) return;
    const response = await catalogSeriesTrialVerify(
      sheet.id,
      {
        ...lastInput,
        revision: sheet.revision,
        calculation_token: result.calculation_token,
        confirmed: true,
        confirm_suggested: suggested,
      },
      options,
    );
    if (response.status !== 201) throw new Error("verify");
    setReceipt(response.data);
    const refreshed = await catalogSeriesSheet(sheet.id, options);
    if (refreshed.status === 200) onSaved(refreshed.data);
    onVerified?.(response.data);
  }
  if (catalog.isPending) return <Loading label="Cargando las opciones de la serie" />;
  if (catalog.isError)
    return (
      <p role="alert">
        No se pudieron cargar las opciones.{" "}
        <Button onClick={() => void catalog.refetch()}>Volver a intentar</Button>
      </p>
    );
  if (!glasses.length || !openings.length)
    return (
      <div>
        <p>
          Completa los perfiles, las aperturas y un vidrio compatible antes de calcular una ventana
          de prueba.
        </p>
        <Button onClick={onComplete}>Completar la serie</Button>
      </div>
    );

  return (
    <section className="series-trial" aria-label="Comparación de la ventana de prueba">
      <header className="series-trial__heading">
        <div>
          <h2>Revisa una ventana de prueba</h2>
          <p>
            {sheet.tabs.rules.name} · Compara con tu manual o con lo que cortas hoy. Si algo no
            calza, revisa el ajuste antes de aplicarlo.
          </p>
        </div>
        <svg
          className="series-trial__drawing"
          role="img"
          aria-label={`Ventana ${domainLabel(selectedOpening)}`}
          viewBox="0 0 120 110"
        >
          <rect x="2" y="2" width="116" height="106" className="series-trial__frame" />
          <rect x="14" y="14" width="92" height="82" className="series-trial__glass" />
          <OpeningSymbol
            opening={legacySymbolOpening(selectedOpening)}
            x={16}
            y={16}
            width={88}
            height={78}
          />
        </svg>
      </header>
      <fieldset disabled={busy} className="series-trial__inputs" onChange={invalidate}>
        <legend>Ventana de prueba</legend>
        <label>
          Ancho · mm
          <input
            className="ui-field__input"
            inputMode="decimal"
            value={width}
            onChange={(event) => setWidth(event.target.value)}
          />
        </label>
        <label>
          Alto · mm
          <input
            className="ui-field__input"
            inputMode="decimal"
            value={height}
            onChange={(event) => setHeight(event.target.value)}
          />
        </label>
        <label>
          Apertura
          <select
            className="ui-field__input"
            value={selectedOpening}
            onChange={(event) => setOpening(event.target.value)}
          >
            {openings.map((value) => (
              <option value={value} key={value}>
                {domainLabel(value)}
              </option>
            ))}
          </select>
        </label>
        <label>
          Vidrio
          <select
            className="ui-field__input"
            value={selectedGlass?.sku}
            onChange={(event) => setGlassSku(event.target.value)}
          >
            {glasses.map((item) => (
              <option key={item.sku} value={item.sku}>
                {item.spec}
              </option>
            ))}
          </select>
        </label>
        <label>
          Color
          <select
            className="ui-field__input"
            value={selectedColor}
            onChange={(event) => setColor(event.target.value)}
          >
            {catalog.data.colors.map((value) => (
              <option key={value} value={value}>
                {domainLabel(value)}
              </option>
            ))}
          </select>
        </label>
      </fieldset>
      {error && <p role="alert">{error}</p>}
      <div>
        <Button variant={result ? "secondary" : "primary"} loading={busy} onClick={compare}>
          {result ? "Comparar medidas" : "Calcular ventana"}
        </Button>
      </div>
      {result && (
        <>
          <TrialMeasurements
            rows={result.measurements}
            manual={manual}
            busy={busy}
            onManual={(key, value) => {
              setManual({ ...manual, [key]: value });
              invalidate();
            }}
            onPropose={propose}
          />
          {choices && (
            <section className="series-trial__proposal" aria-label="Ajustes propuestos">
              <h3>Elige la regla que corresponde a tu taller</h3>
              <p>
                Una medida puede tener varias causas. Revisa cómo cambia todo el despiece antes de
                aplicar.
              </p>
              {!choices.items.length ? (
                <p>
                  No hay un ajuste exacto para esta medida con las reglas disponibles. Revisa la
                  pieza y sus parámetros en la ficha.
                </p>
              ) : (
                <>
                  {choices.items.map((item, index) => (
                    <label key={`${item.change.row_id}:${item.change.field}`}>
                      <input
                        type="radio"
                        name="trial-rule"
                        checked={choice === index}
                        disabled={busy}
                        onChange={() => setChoice(index)}
                      />
                      {item.label}: {fmtMm(item.previous)} → {fmtMm(item.value)} mm
                    </label>
                  ))}
                  {proposal && (
                    <ul>
                      {proposal.measurements
                        .filter(
                          (row) =>
                            result.measurements.find((before) => before.key === row.key)
                              ?.value_mm !== row.value_mm,
                        )
                        .map((row) => {
                          const before = result.measurements.find((item) => item.key === row.key);
                          return (
                            <li key={row.key}>
                              {trialPiece(row)}: {before ? fmtMm(before.value_mm) : "Sin pieza"} →{" "}
                              {fmtMm(row.value_mm)} mm
                            </li>
                          );
                        })}
                    </ul>
                  )}
                  <Button disabled={!proposal} loading={busy} onClick={() => void run(apply)}>
                    Aplicar y recalcular
                  </Button>
                </>
              )}
            </section>
          )}
          <footer className="series-trial__confirmation">
            {receipt ? (
              <p role="status">
                Prueba guardada · {formatDateTime(receipt.verified_at)}. Los próximos cambios se
                compararán con esta ventana.
              </p>
            ) : (
              <>
                <p>
                  Al confirmar, esta ventana queda guardada como prueba de la serie. Si un cambio la
                  altera, te avisamos antes de guardar.
                </p>
                <label>
                  <input
                    type="checkbox"
                    checked={confirmed}
                    disabled={busy || changed || differences || !result.measurements.length}
                    onChange={(event) => setConfirmed(event.target.checked)}
                  />
                  He revisado el despiece completo y corresponde a lo que fabricamos.
                </label>
                {suggestedCount > 0 && (
                  <label>
                    <input
                      type="checkbox"
                      checked={suggested}
                      disabled={busy}
                      onChange={(event) => setSuggested(event.target.checked)}
                    />
                    Confirmo como datos del taller los {suggestedCount} valores sugeridos de esta
                    serie.
                  </label>
                )}
                {changed && <p>Compara las medidas actuales antes de confirmar.</p>}
                {differences && !changed && <p>Ajusta las diferencias antes de confirmar.</p>}
                <Button
                  variant="primary"
                  disabled={
                    !confirmed ||
                    changed ||
                    differences ||
                    !result.measurements.length ||
                    (suggestedCount > 0 && !suggested)
                  }
                  loading={busy}
                  onClick={() => void run(verify)}
                >
                  Confirmar ventana de prueba
                </Button>
              </>
            )}
          </footer>
        </>
      )}
    </section>
  );
}
