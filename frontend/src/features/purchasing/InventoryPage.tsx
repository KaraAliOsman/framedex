import { useCallback, useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useSearchParams } from "react-router-dom";
import { apiMutator } from "../../api/apiMutator";
import type { InventoryStockItem } from "../../api/generated/models";
import { useAuthSession } from "../../auth/AuthSessionProvider";
import { DeniedState, ErrorState, LoadingState, PageHeader, Qty } from "../../ui";
import { InventorySection } from "./InventorySection";
import "./purchasing.css";

const units: Record<string, string> = {
  EA: "un.",
  BAR: "barras",
  KIT: "kits",
  SHEET: "planchas",
  M: "m",
  M2: "m²",
  KG: "kg",
};

export function InventoryPage(): JSX.Element {
  const org = useAuthSession().me?.active_organization;
  if (!org || !["OWNER", "ESTIMATOR", "WORKSHOP_MANAGER", "OPERATOR"].includes(org.role))
    return (
      <DeniedState reason="El dueño, el estimador y el taller pueden consultar inventario. Solicita acceso al dueño." />
    );
  return (
    <InventoryWorkspace
      key={org.id}
      orgId={org.id}
      canWrite={org.role === "OWNER" || org.role === "WORKSHOP_MANAGER"}
    />
  );
}

function InventoryWorkspace({
  orgId,
  canWrite,
}: {
  orgId: string;
  canWrite: boolean;
}): JSX.Element {
  const [params] = useSearchParams();
  const [needle, setNeedle] = useState(params.get("sku") ?? "");
  useEffect(() => setNeedle(params.get("sku") ?? ""), [params]);
  const request = useCallback(
    async <T,>(path: string, method = "GET", body?: unknown): Promise<T> => {
      const result = await apiMutator<{ data: T }>(`/api/v1/${path}`, {
        method,
        headers: { "X-Organization-ID": orgId, "Content-Type": "application/json" },
        body: body === undefined ? undefined : JSON.stringify(body),
      });
      return result.data;
    },
    [orgId],
  );
  const stock = useQuery({
    queryKey: ["inventory-stock", orgId],
    queryFn: async ({ signal }) => {
      const result = await apiMutator<{ data: { items: InventoryStockItem[] } }>(
        "/api/v1/inventory/stock/",
        {
          signal,
          headers: { "X-Organization-ID": orgId },
        },
      );
      return result.data.items;
    },
  });
  const filtered = (stock.data ?? []).filter((item) =>
    [item.sku, item.name, item.spec_text ?? "", item.racks ?? ""]
      .join(" ")
      .toLowerCase()
      .includes(needle.toLowerCase()),
  );
  return (
    <section className="purchasing-page inventory-page" data-density="office">
      <PageHeader
        title="Inventario"
        context="Stock disponible, reservas y retazos de la organización"
      />
      {stock.isPending ? (
        <LoadingState label="Cargando stock" />
      ) : stock.isError ? (
        <ErrorState
          title="No se pudo cargar el stock"
          body="La lista conserva sus registros. Reintenta la consulta."
          onRetry={() => void stock.refetch()}
        />
      ) : (
        <section className="purchasing-stock" aria-label="Stock">
          <h2>Stock</h2>
          <label>
            Buscar por código, nombre o ubicación
            <input type="search" value={needle} onChange={(e) => setNeedle(e.target.value)} />
          </label>
          {stock.data.length === 0 ? (
            <p>No hay stock registrado. El taller puede registrar una recepción o un ajuste.</p>
          ) : filtered.length === 0 ? (
            <p>
              No hay stock con esta búsqueda.{" "}
              <button type="button" onClick={() => setNeedle("")}>
                Ver todo el stock
              </button>
            </p>
          ) : (
            <div
              className="inventory-stock-scroll"
              tabIndex={0}
              role="region"
              aria-label="Detalle de stock"
            >
              <table>
                <thead>
                  <tr>
                    <th>Código</th>
                    <th>Material</th>
                    <th>Existencia</th>
                    <th>Reservado</th>
                    <th>Disponible</th>
                    <th>Por recibir</th>
                    <th>Ubicación</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((item) => (
                    <tr key={`${item.item_id}:${item.variant_key}`}>
                      <td className="ui-value">{item.sku}</td>
                      <td>
                        {item.name}
                        {item.spec_text && <p className="ui-value">{item.spec_text}</p>}
                      </td>
                      {[
                        item.on_hand_qty,
                        item.reserved_qty,
                        item.available_qty,
                        item.incoming_qty,
                      ].map((value, index) => (
                        <td key={index}>
                          <Qty
                            value={value}
                            precision={
                              item.unit === "M" || item.unit === "M2"
                                ? 2
                                : item.unit === "KG"
                                  ? 1
                                  : 0
                            }
                            unit={units[item.unit] ?? "Sin unidad declarada"}
                          />
                        </td>
                      ))}
                      <td>{item.racks || "Sin ubicación registrada"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      )}
      <InventorySection request={request} canWrite={canWrite} stockItems={stock.data ?? []} />
    </section>
  );
}
