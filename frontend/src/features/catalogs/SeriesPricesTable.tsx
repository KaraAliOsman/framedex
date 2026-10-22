import { Link } from "react-router-dom";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { catalogSeriesEditPrices, catalogSeriesPriceHistory } from "../../api/generated/dekopen";
import type { SeriesSheet } from "../../api/generated/models";
import { ApiError } from "../../api/apiMutator";
import { formatDate, formatDateTime } from "../../format";
import { Button, Dialog, Loading } from "../../ui";
import { EditableTable, type TableChange } from "../../ui/EditableTable";
import { catalogSeriesSheet } from "../../api/generated/dekopen";
import { SupplierPriceImport } from "./SupplierPriceImport";

export function SeriesPricesTable({
  orgId,
  sheet,
  onSaved,
  onDirtyChange,
}: {
  orgId: string;
  sheet: SeriesSheet;
  onSaved: (sheet: SeriesSheet) => void;
  onDirtyChange: (dirty: boolean) => void;
}): JSX.Element {
  const [historyId, setHistoryId] = useState<string | null>(null);
  const [importing, setImporting] = useState(false);
  const [importBusy, setImportBusy] = useState(false);
  const [dirty, setDirty] = useState(false);
  const [refreshError, setRefreshError] = useState("");
  async function refresh() {
    setRefreshError("");
    try {
      const response = await catalogSeriesSheet(sheet.id, {
        headers: { "X-Organization-ID": orgId },
      });
      if (response.status !== 200) throw new Error("sheet");
      onSaved(response.data);
    } catch {
      setRefreshError(
        "Los precios se guardaron. No pudimos actualizar la ficha; vuelve a cargarla.",
      );
    }
  }
  const history = useQuery({
    queryKey: ["series-price-history", orgId, sheet.id, historyId, sheet.tabs.prices.items],
    enabled: !!historyId,
    queryFn: async ({ signal }) => {
      const result = await catalogSeriesPriceHistory(sheet.id, historyId!, {
        headers: { "X-Organization-ID": orgId },
        signal,
      });
      if (result.status !== 200) throw new Error("history");
      return result.data.items;
    },
  });
  async function save(changes: TableChange[]) {
    try {
      const result = await catalogSeriesEditPrices(
        sheet.id,
        {
          revision: sheet.revision,
          reason: "Precio editado en la ficha de la serie por el dueño del taller",
          changes: changes.map((change) => ({
            id: change.rowId,
            previous_unit_cost: change.previousValue!,
            unit_cost: change.value!,
          })),
        },
        { headers: { "X-Organization-ID": orgId } },
      );
      if (result.status !== 200) throw new Error("prices");
      onSaved(result.data);
    } catch (error) {
      if (error instanceof ApiError && error.status === 409)
        throw new Error(
          "Un precio cambió. Abre de nuevo la ficha y revisa el valor antes de guardar.",
        );
      throw new Error("No se pudo guardar el lote de precios. Conservamos tus cambios.");
    }
  }
  if (!sheet.tabs.prices.can_view)
    return <p>El dueño administra los precios de compra del taller.</p>;
  return (
    <div className="series-prices">
      <p>
        Precios de compra por unidad, antes de impuestos. Cada cambio queda registrado en{" "}
        <Link to="/pricing/cost-lists?section=audits">el historial de precios</Link>.
      </p>
      <EditableTable
        label="Precios de la serie"
        columns={[
          { id: "sku", label: "Código", readOnly: true },
          { id: "unit", label: "Unidad de compra", readOnly: true },
          { id: "currency", label: "Moneda", readOnly: true },
          {
            id: "unit_cost",
            label: "Precio de compra",
            kind: "decimal",
            precision: 4,
            min: "0",
            max: "9999999999.9999",
          },
        ]}
        rows={sheet.tabs.prices.items.map((item) => ({
          id: item.id,
          label: item.description || item.sku,
          values: {
            sku: item.sku,
            unit:
              { BAR: "Barra", M: "Metro", M2: "m²", KIT: "Kit", UNIT: "Unidad", EA: "Unidad" }[
                item.unit
              ] ?? item.unit,
            currency: item.currency,
            unit_cost: item.unit_cost,
          },
          after: <span>Taller · vigente desde {formatDate(item.valid_from)}</span>,
        }))}
        onSave={save}
        onDirtyChange={(value) => {
          setDirty(value);
          onDirtyChange(value);
        }}
        onHistory={(row) => setHistoryId(row)}
      />
      <Button
        disabled={dirty}
        disabledReason="Guarda o descarta tus cambios antes de importar precios."
        onClick={() => setImporting(true)}
      >
        Importar precios del proveedor
      </Button>
      {refreshError && (
        <p role="alert">
          {refreshError} <Button onClick={() => void refresh()}>Actualizar ficha</Button>
        </p>
      )}
      {importing && (
        <Dialog
          title="Precios del proveedor"
          width="xl"
          onClose={() => {
            if (!importBusy) setImporting(false);
          }}
        >
          <SupplierPriceImport
            key={`${orgId}:${sheet.id}`}
            orgId={orgId}
            initialSupplier={sheet.tabs.rules.manufacturer ?? ""}
            onBusyChange={setImportBusy}
            onApplied={() => void refresh()}
          />
          <Button disabled={importBusy} onClick={() => setImporting(false)}>
            Volver a la serie
          </Button>
        </Dialog>
      )}
      {historyId && (
        <Dialog title="Historial del precio" onClose={() => setHistoryId(null)}>
          {history.isPending ? (
            <Loading label="Cargando el historial" />
          ) : history.isError ? (
            <p role="alert">No se pudo cargar el historial. Cierra y vuelve a intentarlo.</p>
          ) : (
            <ol className="series-sheet__history">
              {history.data.map((entry) => (
                <li key={entry.id}>
                  <strong>{entry.value?.replace(".", ",") ?? "Vacío"}</strong>
                  <p>Anterior: {entry.previous_value?.replace(".", ",") ?? "Vacío"}</p>
                  <p>
                    {entry.actor_name || "Taller"} · {formatDateTime(entry.set_at)}
                  </p>
                  <p>{entry.reason}</p>
                </li>
              ))}
            </ol>
          )}
        </Dialog>
      )}
    </div>
  );
}
