import { useMemo, useState } from "react";
import type { ProductionOrderDetail, ProductionStep } from "../../api/generated/models";
import { DataTable, EmptyState, TechDetails, type TableColumn } from "../../ui";
import { fmtMm, formatDateTime, formatDecimal } from "../../format";
import { domainLabels } from "../../i18n/domainLabels";
import { Link } from "react-router-dom";
import { compareDecimal } from "../../decimal";
import { cutRoleLabel, stationCodeLabel } from "./labels";
import type { WorkOrderOptimization } from "./CutPlanView";

export type WorkshopPiece = {
  id: string;
  identity?: string;
  code: string;
  position: string;
  unit?: number;
  role?: string;
  sku?: string;
  length?: string;
  width?: string;
  height?: string;
  destination: string;
};

/** Display only sealed addresses and engine measurements; no new piece numbers. */
export function orderPieces(detail: ProductionOrderDetail): WorkshopPiece[] {
  const optimization = detail.payload?.optimization as WorkOrderOptimization | undefined;
  const position = detail.making?.code ?? "Sin dato · posición sin código";
  const rows: WorkshopPiece[] = [];
  for (const bar of optimization?.bars?.workshop_cut_plan ?? []) {
    for (const cut of bar.cuts)
      rows.push({
        id: `${bar.bar_index}:${cut.sequence}:${cut.piece_id}`,
        identity: cut.piece_stable_id,
        code: cut.piece_code ?? "Sin dato · pieza sin etiqueta",
        position,
        unit: cut.unit_index,
        role: cut.role,
        sku: cut.workshop_sku,
        length: cut.length_mm,
        destination: `Barra ${bar.bar_index}`,
      });
  }
  for (const sheet of optimization?.sheets ?? []) {
    for (const piece of sheet.placements)
      rows.push({
        id: `lamina:${sheet.sheet_index}:${piece.sequence}:${piece.piece_id}`,
        identity: piece.piece_stable_id,
        code: piece.piece_code ?? "Sin dato · pieza sin etiqueta",
        position,
        unit: piece.unit_index,
        sku: piece.workshop_sku,
        width: piece.width_mm,
        height: piece.height_mm,
        destination: `Lámina ${sheet.sheet_index}`,
      });
  }
  return rows.sort(
    (a, b) =>
      (a.unit ?? 0) - (b.unit ?? 0) || a.code.localeCompare(b.code, "es-CL", { numeric: true }),
  );
}

export function pieceMeasure(piece: WorkshopPiece): string {
  return piece.length
    ? `${fmtMm(piece.length)} mm`
    : piece.width && piece.height
      ? `${fmtMm(piece.width)} × ${fmtMm(piece.height)} mm`
      : "Sin dato · faltan medidas selladas";
}

const columns: TableColumn<WorkshopPiece>[] = [
  { id: "position", label: "Posición", value: (p) => p.position },
  { id: "unit", label: "Unidad", value: (p) => p.unit, numeric: true },
  {
    id: "code",
    label: "Etiqueta de pieza",
    value: (p) => p.code,
    render: (p) => <span className="ui-value">{p.code}</span>,
  },
  { id: "role", label: "Pieza", value: (p) => cutRoleLabel(p.role) },
  { id: "sku", label: "Material", value: (p) => p.sku },
  {
    id: "measure",
    label: "Medida del motor",
    value: pieceMeasure,
    render: (p) => <span className="ui-value">{pieceMeasure(p)}</span>,
  },
  { id: "destination", label: "Origen", value: (p) => p.destination },
];
export function WorkOrderPieces({ pieces }: { pieces: readonly WorkshopPiece[] }) {
  return (
    <DataTable
      rows={pieces}
      columns={columns}
      rowKey={(p) => p.id}
      label="piezas"
      emptyReason="Optimiza la OT para asignar las piezas a barras y láminas con sus etiquetas físicas."
    />
  );
}

export function WorkOrderShortages({
  detail,
  office = false,
}: {
  detail: ProductionOrderDetail;
  office?: boolean;
}) {
  const optimization = detail.payload?.optimization as
    | {
        color?: string;
        stock_reservations?: { sku?: string; name?: string; short?: string; unit?: string }[];
        unmapped_stock_skus?: string[];
      }
    | undefined;
  const short = (optimization?.stock_reservations ?? []).filter(
    (item) => item.short && compareDecimal(item.short, "0") > 0,
  );
  const unmapped = optimization?.unmapped_stock_skus ?? [];
  if (!short.length && !unmapped.length) return null;
  return (
    <section className="production-shortages" aria-label="Qué falta" role="status">
      <h3>Falta material para completar la estación</h3>
      <ul>
        {short.map((item) => (
          <li key={item.sku}>
            <strong>{item.name ?? item.sku ?? "Sin dato · material sin nombre"}</strong>
            <span className="ui-value">
              {formatDecimal(item.short)}{" "}
              {domainLabels[item.unit ?? ""] ?? "Sin dato · unidad no declarada"}
            </span>
            <span>
              Color:{" "}
              {optimization?.color
                ? (domainLabels[optimization.color] ?? "Sin dato · revisa el acabado sellado")
                : "Sin dato · color no declarado"}
            </span>
          </li>
        ))}
      </ul>
      {unmapped.map((sku) => (
        <p key={sku}>{sku} · sin equivalencia de stock. El jefe debe completar el catálogo.</p>
      ))}
      <p>
        La reserva disponible no cubre la OT. El jefe debe comprar o reservar material y volver a
        revisar los faltantes.
      </p>
      {office && detail.project_version_id ? (
        <Link to={`/purchasing?version=${encodeURIComponent(detail.project_version_id)}`}>
          Comprar lo que falta para esta revisión
        </Link>
      ) : null}
    </section>
  );
}

export function WorkOrderStepper({
  steps,
  selectedId,
  onSelect,
}: {
  steps: ProductionStep[];
  selectedId: string | null;
  onSelect: (step: ProductionStep) => void;
}) {
  const first = steps.find((s) => s.status !== "DONE")?.id;
  return (
    <ol className="production-stepper" aria-label="Ruta de fabricación">
      {steps.map((step) => (
        <li key={step.id}>
          <button
            type="button"
            aria-pressed={selectedId === step.id}
            onClick={() => onSelect(step)}
          >
            <span className="ui-value">{formatDecimal(step.sequence)}</span>
            <strong>{stationCodeLabel(step.code)}</strong>
            <span>
              {step.status === "READY" && first !== step.id
                ? "Pendiente"
                : (domainLabels[step.status] ?? "Sin dato · estado no reconocido")}
            </span>
          </button>
        </li>
      ))}
    </ol>
  );
}

const eventLabels: Record<string, string> = {
  WO_RELEASED: "OT liberada",
  STEP_STARTED: "iniciado",
  STEP_COMPLETED: "completado",
  STEP_BLOCKED: "bloqueado",
  STEP_UNBLOCKED: "desbloqueado",
  NOTE: "nota registrada",
  QC_CHECK: "medición registrada",
  QC_FAILED: "rechazado en calidad",
  WO_COMPLETED: "OT completada",
  WO_HOLD: "OT detenida",
  WO_OPTIMIZED: "plan de corte optimizado",
  WO_REMADE: "remake creado",
  WO_PACKED: "embalaje generado",
  WO_CANCELLED: "OT cancelada",
  WO_DISPATCHED: "OT despachada",
  WO_INSTALLED: "instalación confirmada",
  WO_STOCK_CONSUMED: "material consumido",
};

export function WorkOrderHistory({ detail }: { detail: ProductionOrderDetail }) {
  const [station, setStation] = useState("");
  const [query, setQuery] = useState("");
  const events = useMemo(
    () =>
      detail.events
        .filter(
          (e) =>
            (!station || e.step_code === station) &&
            [e.actor_label, e.payload.note, eventLabels[e.event]]
              .join(" ")
              .toLocaleLowerCase("es-CL")
              .includes(query.toLocaleLowerCase("es-CL")),
        )
        .reverse(),
    [detail, station, query],
  );
  return (
    <section className="production-history" aria-label="Trazabilidad humana">
      <div className="production-board-filters">
        <label>
          Estación
          <select value={station} onChange={(e) => setStation(e.target.value)}>
            <option value="">Todas</option>
            {detail.steps.map((s) => (
              <option key={s.id} value={s.code}>
                {stationCodeLabel(s.code)}
              </option>
            ))}
          </select>
        </label>
        <label>
          Persona o motivo
          <input value={query} onChange={(e) => setQuery(e.target.value)} />
        </label>
      </div>
      {events.length ? (
        <ol>
          {events.map((event) => {
            const ops = Array.isArray(event.payload.ops_executed)
              ? event.payload.ops_executed.length
              : null;
            const qc = event.payload.qc_check as
              { check?: string; result?: string; item_code?: string } | undefined;
            return (
              <li key={event.id}>
                <time className="ui-value" dateTime={event.created_at}>
                  {formatDateTime(event.created_at)}
                </time>
                <span>
                  {event.actor_label ?? "Sin dato · autor no registrado"} ·{" "}
                  {event.step_code ? stationCodeLabel(event.step_code) + " " : ""}
                  {eventLabels[event.event] ?? "Evento técnico registrado"}
                  {ops !== null ? ` (${formatDecimal(ops)} operaciones)` : ""}
                </span>
                {typeof event.payload.note === "string" ? (
                  <p>{event.payload.note}</p>
                ) : qc ? (
                  <p>
                    {qc.item_code ? `${qc.item_code} · ` : ""}
                    {qc.check} · {domainLabels[qc.result ?? ""] ?? "Sin dato"}
                  </p>
                ) : null}
                <TechDetails diagnostic={JSON.stringify(event, null, 2)} />
              </li>
            );
          })}
        </ol>
      ) : (
        <EmptyState
          title="Sin eventos para este filtro"
          body="Prueba con otra estación o persona."
        />
      )}
    </section>
  );
}
