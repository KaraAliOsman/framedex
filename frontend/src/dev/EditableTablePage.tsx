import { useState } from "react";

import { Button } from "../ui/Controls";
import { EditableTable, type EditableRow, type TableChange } from "../ui/EditableTable";
import "./editable-table-page.css";

const modes = ["Datos de ejemplo", "Peor caso", "Vacío", "Uno", "300 perfiles"];

function sample(mode: number): EditableRow[] {
  const count = mode === 2 ? 0 : mode === 3 ? 1 : mode === 4 ? 300 : 5;
  const names = [
    "Marco perimetral para ventana practicable con rotura de puente térmico y drenaje",
    "Hoja oscilobatiente reforzada con terminación foliada exterior color roble dorado",
    "Junquillo curvo para termopanel laminado de seguridad en fachada expuesta al viento",
    "Riel inferior con canal de evacuación de agua y encuentro para corredera de tres hojas",
    "Inversor central con burlete de cierre continuo · edición especial para taller Ñuble",
  ];
  return Array.from({ length: count }, (_, index) => ({
    id: String(index),
    label:
      mode === 1 || mode === 4
        ? names[index % names.length]!.slice(0, 80)
        : ["Marco", "Hoja", "Junquillo", "Travesaño", "Inversor"][index]!,
    values: {
      code: `PRO-${String(index + 1).padStart(4, "0")}`,
      width: mode === 1 && index === 1 ? "0.0000" : mode === 1 && index === 2 ? null : "60.1234",
      length: "6500.0001",
    },
    suggested: index % 3 === 0,
    after: <span>{index % 3 === 0 ? "Sugerido" : "Del taller"}</span>,
  }));
}

/** Development only. Deliberate stress inputs never enter a tenant catalog. */
export function EditableTablePage(): JSX.Element {
  const [mode, setMode] = useState(() =>
    Number(new URLSearchParams(location.search).get("data") ?? 0),
  );
  const [rows, setRows] = useState(() => sample(mode));
  async function save(changes: TableChange[]) {
    setRows((current) =>
      current.map((row) => ({
        ...row,
        values: {
          ...row.values,
          ...Object.fromEntries(
            changes
              .filter((change) => change.rowId === row.id)
              .map((change) => [change.columnId, change.value]),
          ),
        },
      })),
    );
  }
  return (
    <main className="editable-table-page">
      <p>Muestra de tabla · valores sintéticos para revisión</p>
      <h1>Perfiles</h1>
      <EditableTable
        key={mode}
        label="Perfiles de ejemplo"
        columns={[
          { id: "code", label: "Código" },
          {
            id: "width",
            label: "Ancho visible",
            kind: "decimal",
            precision: 4,
            min: "0",
            nullable: true,
            unit: "mm",
          },
          {
            id: "length",
            label: "Largo de barra",
            kind: "decimal",
            precision: 4,
            min: "0",
            unit: "mm",
          },
        ]}
        rows={rows}
        onSave={save}
      />
      <nav className="editable-table-page__modes" aria-label="Datos para probar la tabla">
        {modes.map((label, index) => (
          <Button
            key={label}
            size="compact"
            aria-pressed={mode === index}
            onClick={() => {
              setMode(index);
              setRows(sample(index));
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
