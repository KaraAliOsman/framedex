import { useState } from "react";
import { CatalogDoubleReadReview } from "../features/catalogs/CatalogDoubleReadReview";
import type { CatalogReviewRow } from "../features/catalogs/catalogDoubleReadModel";
import { Button } from "../ui";
import "./editable-table-page.css";

const modes = ["Datos de ejemplo", "Peor caso", "Vacío", "Uno", "500 filas"];
const sheets = [
  {
    name: "Perfiles",
    columns: [
      { key: "depth_mm", label: "Profundidad", kind: "positive", required: true, choices: null },
    ],
  },
];

function fixture(mode: number): CatalogReviewRow[] {
  const count = mode === 2 ? 0 : mode === 3 ? 1 : mode === 4 ? 500 : 2;
  return Array.from({ length: count }, (_, index) => ({
    key: String(index),
    row: index + 1,
    sheet: "Perfiles",
    method: "AI",
    confidence: "REVIEW_REQUIRED",
    include: false,
    errors: [],
    warnings: [],
    double_read: { identity_unique: mode !== 1 },
    values: {
      sku: mode === 1 ? "Perfil-ventana-Ñandú-窗-".repeat(4) : index ? "001-窗-Ñandú" : "001",
      depth_mm: null,
    },
    fields: {
      sku: { comparison: "AGREED", readings: [{ value: "001" }, { value: "001" }] },
      depth_mm: {
        comparison: "REVIEW",
        readings: [
          {
            value: mode === 1 ? "200.00" : "60.00",
            ref:
              mode === 1
                ? "Manual-de-perfiles-con-foliado-exterior-y-terminaciones-especiales-".repeat(3) +
                  ".pdf · página 200"
                : "manual-sintético.pdf · página 2",
            quote:
              mode === 1
                ? "Perfil con terminación exterior, certificado según la tabla de medidas para revisión 窗. ".repeat(
                    12,
                  )
                : "Profundidad: 60,00 mm",
            confidence: "HIGH",
          },
          {
            value: "62.00",
            ref: "manual-sintético.pdf · página 8",
            quote: "Profundidad: 62,00 mm",
            confidence: "LOW",
          },
        ],
      },
    },
  }));
}

export function CatalogDoubleReadPage(): JSX.Element {
  const [mode, setMode] = useState(0);
  const [rows, setRows] = useState(() => fixture(0));
  const [opened, setOpened] = useState("");
  return (
    <main className="editable-table-page">
      <h1>Lectura del manual · ensayo visual</h1>
      <p>Propuestas sintéticas para probar las dos citas; no se guardan en el catálogo.</p>
      <CatalogDoubleReadReview
        key={mode}
        rows={rows}
        sheets={sheets}
        disabled={false}
        onPatch={(key, field, value) =>
          setRows((current) =>
            current.map((row) =>
              row.key === key ? { ...row, values: { ...row.values, [field]: value } } : row,
            ),
          )
        }
        onInclude={(key, include) =>
          setRows((current) => current.map((row) => (row.key === key ? { ...row, include } : row)))
        }
        onOpenRow={(row) => setOpened(`Fila ${row.row} seleccionada para la revisión completa`)}
      />
      {opened && <p role="status">{opened}</p>}
      <nav className="editable-table-page__modes" aria-label="Datos para probar la doble lectura">
        {modes.map((label, index) => (
          <Button
            key={label}
            size="compact"
            aria-pressed={mode === index}
            onClick={() => {
              setMode(index);
              setRows(fixture(index));
              setOpened("");
            }}
          >
            {label}
          </Button>
        ))}
      </nav>
    </main>
  );
}
