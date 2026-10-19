import { useState } from "react";
import type { ProductionOrder } from "../../api/generated/models";
import { EmptyState, ErrorState, LoadingState } from "../../ui";
import { formatDate, formatDecimal } from "../../format";
import { domainLabels } from "../../i18n/domainLabels";
import { stationCodeLabel } from "./labels";

export type StationQueueGroup = {
  code?: string;
  entries?: Array<{
    step_id?: string;
    order_id?: string;
    order_code?: string;
    status?: string;
    is_next?: boolean;
    note?: string;
  }>;
};
export function ProductionBoard({
  orders,
  stations,
  onOpen,
  loading,
  error,
  retry,
}: {
  orders: ProductionOrder[];
  stations: StationQueueGroup[];
  onOpen: (id: string) => void;
  loading: boolean;
  error?: string;
  retry: () => void;
}) {
  const [project, setProject] = useState("");
  const [date, setDate] = useState("");
  const [block, setBlock] = useState("");
  const projects = [
    ...new Map(
      orders.filter((o) => o.project_code).map((o) => [o.project_code, o.project_name]),
    ).entries(),
  ];
  const groups = stations.map((station) => ({
    ...station,
    orders: orders.filter(
      (o) =>
        (station.entries ?? []).some((e) => e.order_id === o.id && e.is_next) &&
        (!project || o.project_code === project) &&
        (!date || (!!o.scheduled_date && o.scheduled_date <= date)) &&
        (!block ||
          (block === "hold" && o.status === "HOLD") ||
          (block === "shortage" && o.shortage > 0) ||
          (block === "qc" && o.status === "HOLD" && o.qc_failed) ||
          (block === "plan" && !o.optimization_ready)),
    ),
  }));
  const ended = orders.filter((o) =>
    ["COMPLETED", "DISPATCHED", "INSTALLED", "CANCELLED"].includes(o.status),
  );
  if (loading) return <LoadingState label="Cargando estaciones de producción" />;
  if (error) return <ErrorState title="No se pudo cargar la planta" body={error} onRetry={retry} />;
  if (!orders.length)
    return (
      <EmptyState
        title="No hay OT liberadas"
        body="Libera una revisión habilitada en Preparar producción."
        action={<button onClick={retry}>Actualizar</button>}
      />
    );
  const active = orders.filter((o) => !ended.includes(o));
  const causes = [
    {
      key: "plan",
      count: active.filter((o) => !o.optimization_ready).length,
      label: "sin plan de corte",
      action: "Ver cuáles",
    },
    {
      key: "shortage",
      count: active.filter((o) => o.shortage > 0).length,
      label: "con falta de material",
      action: "Ver cuáles",
    },
    {
      key: "qc",
      count: active.filter((o) => o.status === "HOLD" && o.qc_failed).length,
      label: "rechazadas en calidad",
      action: "Ver cuáles",
    },
    {
      key: "hold",
      count: active.filter((o) => o.status === "HOLD" && !o.qc_failed).length,
      label: "bloqueadas",
      action: "Ver cuáles",
    },
  ].filter((cause) => cause.count > 0);
  return (
    <section className="production-board" aria-label="Tablero por estación">
      {causes.length ? (
        <ul className="production-causes" aria-label="Decisiones pendientes">
          {causes.map((cause) => (
            <li key={cause.key}>
              <strong className="ui-value">{formatDecimal(cause.count)}</strong>{" "}
              {cause.count === 1 ? "orden" : "órdenes"} {cause.label}
              <button
                type="button"
                className="link-button"
                aria-pressed={block === cause.key}
                onClick={() => setBlock(block === cause.key ? "" : cause.key)}
              >
                {block === cause.key ? "Ver todas" : cause.action}
              </button>
            </li>
          ))}
        </ul>
      ) : null}
      <div className="production-board-filters">
        <label>
          Obra
          <select value={project} onChange={(e) => setProject(e.target.value)}>
            <option value="">Todas las obras</option>
            {projects.map(([code, name]) => (
              <option key={code} value={code!}>
                {name ?? code}
              </option>
            ))}
          </select>
        </label>
        <label>
          Compromiso hasta
          <input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
        </label>
        <label>
          Requiere persona
          <select value={block} onChange={(e) => setBlock(e.target.value)}>
            <option value="">Todas las OT</option>
            <option value="hold">Bloqueadas</option>
            <option value="shortage">Falta material</option>
            <option value="qc">Calidad rechazada</option>
            <option value="plan">Sin plan de corte</option>
          </select>
        </label>
        <button type="button" onClick={retry}>
          Actualizar tablero
        </button>
      </div>
      <div className="production-board-columns">
        {groups.map((station) => (
          <section
            className="production-board-station"
            key={station.code}
            aria-label={stationCodeLabel(station.code)}
          >
            <header>
              <h2>{stationCodeLabel(station.code)}</h2>
              <span className="ui-value">{formatDecimal(station.orders.length)} OT</span>
            </header>
            <div className="production-board-cards">
              {station.orders.length ? (
                station.orders.map((order) => {
                  const entry = station.entries?.find((e) => e.order_id === order.id && e.is_next);
                  return (
                    <button
                      type="button"
                      className="production-board-order"
                      key={order.id}
                      onClick={() => onOpen(order.id)}
                    >
                      <strong className="production-board-work">
                        {order.project_name ?? order.project_code ?? "Obra no vinculada"}
                      </strong>
                      <span className="production-board-meta">
                        {order.client_name ? `${order.client_name} · ` : ""}
                        <span className="ui-value">{order.order_code}</span>
                      </span>
                      <span className="production-board-next">
                        Siguiente: {order.next_step?.label ?? stationCodeLabel(station.code)}
                      </span>
                      <span className="production-board-line ui-value">
                        {formatDecimal(order.quantity)} unidades · {order.steps_done}/
                        {order.steps_total} pasos
                      </span>
                      <span className="ui-value">
                        {order.scheduled_date
                          ? `Compromiso ${formatDate(order.scheduled_date)}`
                          : "Sin dato · agenda de entrega pendiente"}
                      </span>
                      <span>{domainLabels[order.status] ?? "Sin dato · estado sin etiqueta"}</span>
                      {order.status === "HOLD" ? (
                        <span className="production-requires-person">
                          {entry?.note ?? "Bloqueada · revisar motivo"}
                        </span>
                      ) : null}
                      {order.shortage > 0 ? (
                        <span className="production-requires-person">
                          Falta material · {formatDecimal(order.shortage)} necesidades
                        </span>
                      ) : null}
                      {!order.optimization_ready ? (
                        <span className="production-requires-person">Sin plan de corte</span>
                      ) : null}
                      {order.status === "HOLD" && order.qc_failed ? (
                        <span className="production-requires-person">
                          Calidad · requiere supervisor
                        </span>
                      ) : null}
                    </button>
                  );
                })
              ) : (
                <p className="production-board-empty">Sin OT en este filtro.</p>
              )}
            </div>
          </section>
        ))}
      </div>
      {!groups.some((g) => g.orders.length) ? (
        <EmptyState
          title="No hay trabajo activo en este filtro"
          body="Cambia la obra, el compromiso o el motivo de bloqueo."
        />
      ) : null}
      {ended.length ? (
        <details className="production-closed">
          <summary>OT terminadas y canceladas</summary>
          <ul>
            {ended.map((o) => (
              <li key={o.id}>
                <button type="button" onClick={() => onOpen(o.id)}>
                  {o.order_code} · {domainLabels[o.status] ?? "Sin dato"}
                </button>
              </li>
            ))}
          </ul>
        </details>
      ) : null}
    </section>
  );
}
