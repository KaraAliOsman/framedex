import { useState } from "react";
import type { TrialMeasurement } from "../../api/generated/models";
import { compareDecimal, parseDecimalInput } from "../../decimal";
import { fmtMm } from "../../format";
import { domainLabel } from "../../i18n/domainLabels";
import { Button } from "../../ui";

export function trialPiece(row: TrialMeasurement): string {
  const group =
    row.group === "reinforcements"
      ? "Refuerzo"
      : row.group === "glasses"
        ? "Vidrio"
        : domainLabel(row.role);
  const dimension =
    row.field === "width_mm" ? "ancho" : row.field === "height_mm" ? "alto" : "largo";
  return `${group} · ${row.sku} · ${dimension} ${row.index + 1}`;
}

/** Presentation only: all dimensions, quantities and comparisons come from the engine API. */
export function TrialMeasurements({
  rows,
  manual,
  busy,
  onManual,
  onPropose,
}: {
  rows: TrialMeasurement[];
  manual: Record<string, string>;
  busy: boolean;
  onManual: (key: string, value: string) => void;
  onPropose: (row: TrialMeasurement) => void;
}): JSX.Element {
  const [page, setPage] = useState(0);
  const pages = Math.max(1, Math.ceil(rows.length / 50));
  const current = Math.min(page, pages - 1);
  return (
    <>
      <div
        className="series-trial__scroll"
        role="region"
        aria-label="Despiece de la ventana de prueba"
        tabIndex={0}
      >
        <table className="series-trial__table">
          <thead>
            <tr>
              <th>Pieza</th>
              <th>Cant.</th>
              <th>DEKOPEN calcula · mm</th>
              <th>Ángulos</th>
              <th>Según tu manual · mm</th>
              <th>Estado</th>
            </tr>
          </thead>
          <tbody>
            {!rows.length && (
              <tr>
                <td colSpan={6}>
                  El motor no devolvió piezas para esta ventana. Revisa las opciones de la serie.
                </td>
              </tr>
            )}
            {rows.slice(current * 50, (current + 1) * 50).map((row) => {
              const raw = manual[row.key] ?? "",
                value = parseDecimalInput(raw, 2);
              const updated =
                value !== null &&
                row.manual_mm !== null &&
                compareDecimal(value, row.manual_mm) === 0;
              const matches = updated ? row.matches : null;
              return (
                <tr key={row.key} data-changed={matches === false}>
                  <th scope="row">{trialPiece(row)}</th>
                  <td>{row.quantity}</td>
                  <td>{fmtMm(row.value_mm)}</td>
                  <td>
                    {row.angle_left && row.angle_right
                      ? `${fmtMm(row.angle_left)}° / ${fmtMm(row.angle_right)}°`
                      : "No aplica"}
                  </td>
                  <td>
                    <input
                      className="ui-field__input"
                      aria-label={`${trialPiece(row)} según tu manual`}
                      inputMode="decimal"
                      value={raw}
                      disabled={busy}
                      onChange={(event) => onManual(row.key, event.target.value)}
                    />
                  </td>
                  <td>
                    <span>
                      {matches === true
                        ? "Coincide"
                        : matches === false
                          ? `${fmtMm(row.difference_mm!)} mm de diferencia`
                          : raw
                            ? "Por comparar"
                            : "Sin comparar"}
                    </span>
                    {value && compareDecimal(value, row.value_mm) !== 0 && (
                      <Button disabled={busy} onClick={() => onPropose(row)}>
                        Ajustar regla
                      </Button>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      {pages > 1 && (
        <nav className="series-trial__pagination" aria-label="Páginas del despiece">
          <Button disabled={busy || current === 0} onClick={() => setPage(current - 1)}>
            Anterior
          </Button>
          <span role="status">
            Página {current + 1} de {pages} · {rows.length} medidas
          </span>
          <Button disabled={busy || current === pages - 1} onClick={() => setPage(current + 1)}>
            Siguiente
          </Button>
        </nav>
      )}
    </>
  );
}
