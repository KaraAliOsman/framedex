import { useState } from "react";
import type { TrialMeasurement } from "../api/generated/models";
import { Button } from "../ui";
import { TrialMeasurements } from "../features/catalogs/TrialMeasurements";
import "../features/catalogs/series-trial.css";
import "./editable-table-page.css";
import "./series-trial-page.css";

const modes = ["Datos de ejemplo", "Peor caso", "Vacío", "Uno", "500 piezas"];
function sample(mode: number): TrialMeasurement[] {
  const count = mode === 2 ? 0 : mode === 3 ? 1 : mode === 4 ? 500 : 6;
  const codes = [
    "CODIGO".repeat(14),
    "Ñandú-窗-🚪",
    "001",
    "A",
    "Marco muy largo con terminación foliada exterior y drenaje",
  ];
  return Array.from({ length: count }, (_, index) => ({
    key: `profile_cuts:${index}:length_mm`,
    group: "profile_cuts",
    index,
    field: "length_mm",
    role: "FRAME",
    sku: mode === 0 ? `M-${index + 1}` : codes[index % codes.length]!,
    quantity: mode === 0 || mode === 3 ? 1 : index === 0 ? 999999 : 2,
    value_mm: mode === 0 ? "1206.00" : "99999999.99",
    angle_left: "45",
    angle_right: "45",
    manual_mm: null,
    difference_mm: null,
    matches: null,
  }));
}

/** Deliberate display fixtures. Never connected to a tenant or calculation endpoint. */
export function SeriesTrialPage(): JSX.Element {
  const [mode, setMode] = useState(() =>
    Number(new URLSearchParams(location.search).get("data") ?? 0),
  );
  const [manual, setManual] = useState<Record<string, string>>({});
  return (
    <main className="editable-table-page series-trial">
      <p>Ventana de prueba · datos sintéticos para revisión visual</p>
      <h1>Revisa el despiece</h1>
      <TrialMeasurements
        key={mode}
        rows={sample(mode)}
        manual={manual}
        busy={false}
        onManual={(key, value) => setManual({ ...manual, [key]: value })}
        onPropose={() => undefined}
      />
      <nav
        className="editable-table-page__modes series-trial-page__modes"
        aria-label="Datos para probar el despiece"
      >
        {modes.map((label, index) => (
          <Button
            key={label}
            size="compact"
            aria-pressed={mode === index}
            onClick={() => {
              setMode(index);
              setManual({});
              history.replaceState(null, "", `?data=${index}`);
            }}
          >
            {label}
          </Button>
        ))}
      </nav>
    </main>
  );
}
