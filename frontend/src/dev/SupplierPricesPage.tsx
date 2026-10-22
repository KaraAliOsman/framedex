import { useState } from "react";
import { SupplierPricePreview } from "../features/catalogs/SupplierPriceImport";
import { Button } from "../ui";
import "./editable-table-page.css";
import "./supplier-prices-page.css";

const modes = ["Datos de ejemplo", "Peor caso", "Vacío", "Uno", "500 precios"];
const mapping = { sku: "Código", description: "Descripción", unit: "Unidad", unit_cost: "Precio" };

export function SupplierPricesPage(): JSX.Element {
  const [mode, setMode] = useState(0);
  const total = mode === 2 ? 0 : mode === 3 ? 1 : mode === 4 ? 500 : 10;
  const items = Array.from({ length: Math.min(total, 10) }, (_, index) => ({
    sku: mode === 0 ? `PRO-${index}` : index === 0 ? "C".repeat(100) : "001-窗-Ñandú-🚪",
    description:
      mode === 0
        ? "Marco sintético para revisión"
        : "Perfil con foliado exterior y terminación especial 窗 🚪 ".repeat(16),
    unit: "BAR",
    unit_cost: mode === 0 ? "12000.1234" : "9999999999.9999",
    origin: "WORKSHOP" as const,
  }));
  return (
    <main className="editable-table-page supplier-prices">
      <h1>Precios del proveedor · ensayo visual</h1>
      <p>Datos sintéticos. La muestra conserva hasta diez filas aunque el archivo tenga más.</p>
      <SupplierPricePreview
        inspection={{
          columns: Object.values(mapping),
          sheet: "Ensayo",
          suggested_mapping: mapping,
          preview: [],
          total,
        }}
        mapping={mapping}
        preview={{ items, total, applied: false, review_token: null }}
        currency="CLP"
      />
      <nav
        className="editable-table-page__modes supplier-prices-page__modes"
        aria-label="Datos para probar los precios"
      >
        {modes.map((label, index) => (
          <Button
            key={label}
            size="compact"
            aria-pressed={mode === index}
            onClick={() => setMode(index)}
          >
            {label}
          </Button>
        ))}
      </nav>
    </main>
  );
}
