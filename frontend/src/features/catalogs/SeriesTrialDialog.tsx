import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { engineCalculate, projectDesignOptions } from "../../api/generated/dekopen";
import type { EngineCalculateResponse, SeriesSheet } from "../../api/generated/models";
import { parseDecimalInput, compareDecimal } from "../../decimal";
import { fmtMm } from "../../format";
import { domainLabel } from "../../i18n/domainLabels";
import { Button, Dialog, Loading } from "../../ui";
import { ValidatedForm } from "../../ui/FormValidation";

/** A real engine preview; P03 adds the workshop verification receipt. */
export function SeriesTrialDialog({
  orgId,
  sheet,
  onClose,
  onComplete,
}: {
  orgId: string;
  sheet: SeriesSheet;
  onClose: () => void;
  onComplete: () => void;
}): JSX.Element {
  const [result, setResult] = useState<EngineCalculateResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const options = useQuery({
    queryKey: ["series-trial-options", orgId, sheet.id, sheet.revision],
    queryFn: async ({ signal }) => {
      const response = await projectDesignOptions(sheet.id, {
        headers: { "X-Organization-ID": orgId },
        signal,
      });
      if (response.status !== 200) throw new Error("options");
      return response.data;
    },
  });
  const glasses =
    options.data?.glass_specs.filter(
      (item) => item.compatible !== false && item.spec && item.total_thickness_mm,
    ) ?? [];
  const openings =
    options.data?.compatible_openings.filter((code) =>
      [
        "FIXED",
        "TURN_LEFT",
        "TURN_RIGHT",
        "TILT_TOP",
        "TILT_TURN_LEFT",
        "TILT_TURN_RIGHT",
      ].includes(code),
    ) ?? [];
  async function calculate(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    const values = new FormData(event.currentTarget);
    const width = parseDecimalInput(String(values.get("width")), 2);
    const height = parseDecimalInput(String(values.get("height")), 2);
    const glass = glasses.find((item) => item.sku === values.get("glass"));
    setResult(null);
    if (!width || !height || compareDecimal(width, "0") <= 0 || compareDecimal(height, "0") <= 0) {
      setError("Escribe medidas mayores que cero, con hasta dos decimales.");
      return;
    }
    if (!glass) return;
    setError("");
    setBusy(true);
    try {
      const response = await engineCalculate(
        {
          system_id: sheet.id,
          nominal_width_mm: width,
          nominal_height_mm: height,
          color: String(values.get("color")),
          parametric_tree: {
            id: "trial",
            type: "BAY",
            opening_type: String(values.get("opening")),
            glass_spec: glass.spec,
            glass_article_sku: glass.sku,
            glass_thickness_mm: glass.total_thickness_mm,
          },
        },
        { headers: { "X-Organization-ID": orgId } },
      );
      if (response.status !== 200) throw new Error("calculate");
      setResult(response.data);
    } catch {
      setError(
        "La ventana no se pudo calcular. Revisa sus medidas, perfiles, vidrio y reglas de la serie.",
      );
    } finally {
      setBusy(false);
    }
  }
  return (
    <Dialog
      title="Ventana de prueba"
      onClose={() => {
        if (!busy) onClose();
      }}
    >
      {options.isPending ? (
        <Loading label="Cargando las opciones de la serie" />
      ) : options.isError ? (
        <p role="alert">No se pudieron cargar las opciones. Cierra y vuelve a intentarlo.</p>
      ) : glasses.length === 0 || openings.length === 0 ? (
        <div>
          <p>
            Completa los perfiles, las aperturas y un vidrio compatible antes de calcular una
            ventana de prueba.
          </p>
          <Button onClick={onComplete}>Completar la serie</Button>
        </div>
      ) : (
        <ValidatedForm
          className="series-catalog__create"
          onSubmit={(event) => void calculate(event)}
          onChange={() => setResult(null)}
        >
          <p>Comprueba el despiece calculado con los datos actuales de {sheet.tabs.rules.name}.</p>
          <label>
            Ancho · mm
            <input name="width" inputMode="decimal" defaultValue="1200" required disabled={busy} />
          </label>
          <label>
            Alto · mm
            <input name="height" inputMode="decimal" defaultValue="1100" required disabled={busy} />
          </label>
          <label>
            Apertura
            <select name="opening" disabled={busy}>
              {openings.map((opening) => (
                <option key={opening} value={opening}>
                  {domainLabel(opening)}
                </option>
              ))}
            </select>
          </label>
          <label>
            Vidrio
            <select name="glass" disabled={busy}>
              {glasses.map((glass) => (
                <option key={glass.sku} value={glass.sku}>
                  {glass.spec}
                </option>
              ))}
            </select>
          </label>
          <label>
            Color
            <select name="color" disabled={busy}>
              {options.data.colors.map((color) => (
                <option key={color} value={color}>
                  {domainLabel(color)}
                </option>
              ))}
            </select>
          </label>
          {error && <p role="alert">{error}</p>}
          <Button type="submit" variant="primary" loading={busy}>
            Calcular ventana
          </Button>
        </ValidatedForm>
      )}
      {result && (
        <section aria-label="Despiece de la ventana de prueba">
          <h2>Despiece calculado</h2>
          <ul>
            {result.profile_cuts.map((cut, index) => (
              <li key={index}>
                {cut.sku}: {cut.qty} piezas de {fmtMm(cut.length_mm)} mm
              </li>
            ))}
            {result.glasses.map((glass, index) => (
              <li key={`glass-${index}`}>
                Vidrio: {fmtMm(glass.width_mm)} × {fmtMm(glass.height_mm)} mm
              </li>
            ))}
          </ul>
          {!!result.assumptions?.length && (
            <p>
              El cálculo utiliza {result.assumptions.length} valores sugeridos. Confírmalos antes de
              fabricar.
            </p>
          )}
        </section>
      )}
    </Dialog>
  );
}
