import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  analyticsActualReport,
  analyticsActualReportPreview,
  analyticsActualReportSave,
} from "../../api/generated/dekopen";
import type { ActualReportRequestRequest } from "../../api/generated/models";
import { ApiError } from "../../api/apiMutator";
import { domainLabel } from "../../i18n/domainLabels";
import { decimalInputValue, parseDecimalInput } from "../../decimal";
import {
  Button,
  Dialog,
  DeniedState,
  ErrorState,
  LoadingState,
  BlockedState,
  Money,
  Qty,
  ValidatedForm,
  validators,
} from "../../ui";
import { actionErrorDetail } from "../errors";
import type { ActualOrder } from "./types";

function input(value: string | null | undefined): string {
  return decimalInputValue(value).replace(".", ",");
}
function decimal(value: FormDataEntryValue | null): string | null {
  const text = String(value ?? "").trim();
  return text ? parseDecimalInput(text, 8) : null;
}

export function CostClosure({
  orderId,
  onClose,
  onSaved,
  focusId,
}: {
  orderId: string;
  onClose: () => void;
  onSaved: () => void;
  focusId?: string;
}): JSX.Element {
  const [order, setOrder] = useState<ActualOrder>();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [denied, setDenied] = useState(false);
  const [busy, setBusy] = useState(false);
  const [preview, setPreview] = useState<ActualOrder>();
  const [request, setRequest] = useState<ActualReportRequestRequest>();
  const [readAttempt, setReadAttempt] = useState(0);
  useEffect(() => {
    if (order && focusId)
      document
        .querySelector<HTMLElement>(`[data-evidence="${CSS.escape(focusId)}"]`)
        ?.scrollIntoView({ block: "nearest" });
  }, [order, focusId]);
  useEffect(() => {
    let current = true;
    setLoading(true);
    setError("");
    setDenied(false);
    void analyticsActualReport(orderId)
      .then((r) => {
        if (current) setOrder(r.data as unknown as ActualOrder);
      })
      .catch((e) => {
        if (!current) return;
        if (e instanceof ApiError && e.status === 403) setDenied(true);
        else
          setError(
            actionErrorDetail(
              e,
              "No pudimos leer los consumos de esta OT. Actualiza y vuelve a intentar.",
            ),
          );
      })
      .finally(() => {
        if (current) setLoading(false);
      });
    return () => {
      current = false;
    };
  }, [orderId, readAttempt]);
  async function prepare(form: HTMLFormElement) {
    if (!order || order.currency === null) return;
    setBusy(true);
    setError("");
    const fields = new FormData(form);
    const body: ActualReportRequestRequest = {
      request_key: crypto.randomUUID(),
      expected_revision: order.revision,
      source_fingerprint: order.source_fingerprint,
      currency: order.currency,
      source: String(fields.get("source") ?? ""),
      reason: String(fields.get("reason") ?? ""),
      closed: fields.get("closed") === "on",
      materials: order.materials.map((m, index) => ({
        id: m.id,
        unit_cost: decimal(fields.get(`cost${index}`)),
        waste_quantity: decimal(fields.get(`waste${index}`)),
      })),
      labor: order.labor.map((s, index) => ({
        id: s.id,
        hours: decimal(fields.get(`hours${index}`)),
        hourly_rate: decimal(fields.get(`rate${index}`)),
      })),
      other_cost: decimal(fields.get("other")),
      reusable_credit: decimal(fields.get("credit")),
      bars: {
        complete: fields.get("bars_complete") === "on",
        input_mm: decimal(fields.get("input_mm")),
        productive_mm: decimal(fields.get("productive_mm")),
        waste_mm: decimal(fields.get("waste_mm")),
        reusable_mm: decimal(fields.get("reusable_mm")),
      },
    };
    try {
      const response = await analyticsActualReportPreview(orderId, body);
      setPreview(response.data as unknown as ActualOrder);
      setRequest(body);
    } catch (e) {
      setError(
        actionErrorDetail(
          e,
          "No pudimos preparar el registro. Revisa las cantidades y sus referencias.",
        ),
      );
    } finally {
      setBusy(false);
    }
  }
  async function save() {
    if (!request) return;
    setBusy(true);
    setError("");
    try {
      await analyticsActualReportSave(orderId, { ...request, confirmed: true });
      onSaved();
    } catch (e) {
      setError(
        actionErrorDetail(e, "No pudimos registrar el cierre. Actualiza y revisa otra vez."),
      );
      setPreview(undefined);
      setRequest(undefined);
    } finally {
      setBusy(false);
    }
  }
  const validation = Object.fromEntries(
    [
      ...(order?.materials.flatMap((_, i) => [`cost${i}`, `waste${i}`]) ?? []),
      ...(order?.labor.flatMap((_, i) => [`hours${i}`, `rate${i}`]) ?? []),
      "other",
      "credit",
      "input_mm",
      "productive_mm",
      "waste_mm",
      "reusable_mm",
    ].map((name) => [name, validators.decimal(8)]),
  );
  const currency = order?.currency;
  const hasCurrency = currency != null;
  return (
    <Dialog
      title={order ? `${order.code} · Costos reales` : "Consumos y costos de la OT"}
      width="l"
      onClose={onClose}
    >
      {loading ? (
        <LoadingState label="Leyendo el inventario y las estaciones" />
      ) : denied ? (
        <DeniedState reason="El dueño y el jefe de taller registran y leen costos reales." />
      ) : order && currency == null ? (
        <BlockedState
          reason="Falta moneda en la revisión emitida. Crea una revisión con moneda declarada antes de valorar consumos. Ese importe no está registrado en el historial."
          action={
            <Link to={`/projects/${order.project_id}?section=quote`}>
              Abrir revisión de la obra
            </Link>
          }
        />
      ) : order && hasCurrency ? (
        <>
          <p>
            Las cantidades provienen del inventario. Declara el costo neto por su misma unidad y las
            horas de personas realmente imputadas. Los campos vacíos quedan pendientes.
          </p>
          {order.result.cost !== null && !preview && (
            <section className="analytics-ledger">
              <h3>Valor registrado por movimiento y estación</h3>
              <p>
                Origen: {order.source}. La parte perdida ya está incluida en el costo del consumo.
              </p>
              <ul>
                {order.result.lines.map((line) => {
                  const material = order.materials.find((m) => m.id === line.id);
                  const station = order.labor.find((s) => s.id === line.id);
                  return (
                    <li key={line.id} data-evidence={line.id} data-highlight={line.id === focusId}>
                      <strong>{material?.sku ?? station?.label}</strong>
                      <span>
                        {material ? (
                          <>
                            {material.kind === "REMNANT"
                              ? "Retazo consumido"
                              : domainLabel(material.kind)}{" "}
                            ·{" "}
                            <Qty
                              value={line.quantity}
                              unit={domainLabel(material.unit)}
                              precision={2}
                            />{" "}
                            × <Money value={line.unit_cost} currency={currency} />
                          </>
                        ) : (
                          <>
                            <Qty value={line.hours} unit="h" precision={2} /> ×{" "}
                            <Money value={line.hourly_rate} currency={currency} />
                          </>
                        )}
                      </span>
                      <span>
                        Costo: <Money value={line.amount} currency={currency} />
                        {line.waste !== undefined && (
                          <>
                            {" "}
                            · Incluye merma: <Money value={line.waste} currency={currency} />
                          </>
                        )}
                      </span>
                    </li>
                  );
                })}
              </ul>
              <p data-evidence="other" data-highlight={focusId === "other"}>
                Servicios declarados: <Money value={order.other_cost} currency={currency} />
              </p>
              <p data-evidence="credit" data-highlight={focusId === "credit"}>
                Crédito respaldado por retazos:{" "}
                <Money value={order.reusable_credit} currency={currency} />
              </p>
              <p>
                Costo real = consumos − devoluciones + horas + servicios − crédito:{" "}
                <Money value={order.result.cost} currency={currency} />
              </p>
            </section>
          )}
          {preview ? (
            <section className="analytics-preview">
              <h3>Revisa la nueva evidencia</h3>
              <dl>
                <div>
                  <dt>Costo anterior</dt>
                  <dd>
                    <Money value={preview.previous_result?.cost} currency={currency} />
                  </dd>
                </div>
                <div>
                  <dt>Costo propuesto</dt>
                  <dd>
                    <Money value={preview.result.cost} currency={currency} />
                  </dd>
                </div>
              </dl>
              {preview.result.causes.map((c) => (
                <p key={c}>{c}</p>
              ))}
              <p>Origen: {preview.source}</p>
              <p>Motivo: {preview.reason}</p>
              <p>
                Registrar conserva esta evidencia. Una corrección agrega otra revisión; no cambia el
                inventario ni la cotización emitida.
              </p>
              <div className="analytics-actions">
                <Button
                  onClick={() => {
                    setPreview(undefined);
                    setRequest(undefined);
                  }}
                >
                  Volver a los datos
                </Button>
                <Button variant="primary" loading={busy} onClick={() => void save()}>
                  Registrar revisión de costos
                </Button>
              </div>
            </section>
          ) : (
            <ValidatedForm
              className="analytics-closure"
              validators={validation}
              onSubmit={(e) => {
                e.preventDefault();
                void prepare(e.currentTarget);
              }}
            >
              <fieldset>
                <legend>Material consumido</legend>
                {!order.materials.length && (
                  <p>
                    No hay consumos de inventario asociados. Completa las estaciones o registra el
                    consumo real antes del cierre.
                    <Link to={`/production?order=${order.id}`}>
                      Abrir las estaciones de esta OT
                    </Link>
                  </p>
                )}
                {order.materials.map((m, index) => (
                  <div className="analytics-input-row" key={m.id}>
                    <div>
                      <strong>{m.sku}</strong>
                      <span>
                        {m.kind === "REMNANT" ? "Retazo consumido" : domainLabel(m.kind)} ·{" "}
                        <Qty value={m.quantity} unit={domainLabel(m.unit)} precision={2} />
                      </span>
                      <small>{m.name}</small>
                    </div>
                    <label>
                      Costo neto por {domainLabel(m.unit).toLowerCase()} ({order.currency})
                      <input
                        name={`cost${index}`}
                        inputMode="decimal"
                        defaultValue={input(m.unit_cost)}
                      />
                    </label>
                    <label>
                      Parte perdida ({domainLabel(m.unit).toLowerCase()})
                      <input
                        name={`waste${index}`}
                        inputMode="decimal"
                        defaultValue={input(m.waste_quantity)}
                      />
                    </label>
                  </div>
                ))}
                <p>
                  La parte perdida del consumo asigna su costo a merma. Una pérdida adicional
                  registrada en inventario se valora una vez; una devolución resta costo.
                </p>
              </fieldset>
              <fieldset>
                <legend>Horas de personas por estación</legend>
                <p>
                  El tiempo entre inicio y término incluye esperas. Registra horas efectivas de
                  todas las personas, con la tarifa neta que las respalda.
                </p>
                {order.labor.map((s, index) => (
                  <div className="analytics-input-row" key={s.id}>
                    <div>
                      <strong>{s.label}</strong>
                      <span>{domainLabel(s.status)}</span>
                    </div>
                    <label>
                      Horas efectivas
                      <input
                        name={`hours${index}`}
                        inputMode="decimal"
                        defaultValue={input(s.hours)}
                      />
                    </label>
                    <label>
                      Costo por hora ({order.currency})
                      <input
                        name={`rate${index}`}
                        inputMode="decimal"
                        defaultValue={input(s.hourly_rate)}
                      />
                    </label>
                  </div>
                ))}
              </fieldset>
              <fieldset>
                <legend>Servicios y material recuperado</legend>
                <div className="analytics-input-row">
                  <label>
                    Servicios y otros costos netos ({order.currency})
                    <input
                      name="other"
                      inputMode="decimal"
                      defaultValue={input(order.other_cost)}
                    />
                  </label>
                  <label>
                    Crédito por retazos producidos ({order.currency})
                    <input
                      name="credit"
                      inputMode="decimal"
                      defaultValue={input(order.reusable_credit)}
                    />
                  </label>
                </div>
                <p>
                  Declara cero cuando la evidencia respalde que no hubo costo o crédito. Retazos
                  producidos:{" "}
                  {order.produced.length
                    ? order.produced.map((r) => r.code).join(", ")
                    : "ninguno registrado"}
                  .
                </p>
              </fieldset>
              <details>
                <summary>Medición real del corte de barras</summary>
                <p>
                  Entrada = piezas útiles + pérdida + retazo recuperable. Incluye sierra y despuntes
                  en la pérdida. Esta declaración debe cubrir todas las barras de la OT; no incluye
                  láminas.
                </p>
                <div className="analytics-input-row">
                  {(
                    [
                      ["input_mm", "Entrada total"],
                      ["productive_mm", "Largo en piezas"],
                      ["waste_mm", "Pérdida total"],
                      ["reusable_mm", "Retazo recuperable"],
                    ] as const
                  ).map(([key, label]) => (
                    <label key={key}>
                      {label} (mm)
                      <input name={key} inputMode="decimal" defaultValue={input(order.bars[key])} />
                    </label>
                  ))}
                </div>
                <label className="analytics-check">
                  <input
                    name="bars_complete"
                    type="checkbox"
                    defaultChecked={order.bars.complete}
                  />
                  Confirmo que la medición incluye todas las barras cortadas para esta OT.
                </label>
              </details>
              <label>
                Origen de las tarifas, horas y mediciones
                <input
                  name="source"
                  required
                  minLength={3}
                  maxLength={1000}
                  defaultValue={order.source}
                />
              </label>
              <label>
                Motivo de este registro
                <input name="reason" required minLength={3} maxLength={1000} defaultValue="" />
              </label>
              <label className="analytics-check">
                <input name="closed" type="checkbox" defaultChecked={order.closed} />
                Confirmo que los consumos, devoluciones, horas y servicios de esta OT están
                completos.
              </label>
              <p>
                Sin esa confirmación puedes conservar evidencia parcial; el margen no se podrá
                calcular.
              </p>
              <Button variant="primary" type="submit" loading={busy}>
                Revisar registro de costos
              </Button>
            </ValidatedForm>
          )}
        </>
      ) : null}
      {error && (
        <ErrorState
          body={error}
          onRetry={!order ? () => setReadAttempt((attempt) => attempt + 1) : undefined}
        />
      )}
    </Dialog>
  );
}
