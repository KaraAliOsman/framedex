import { useCallback, useEffect, useLayoutEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { analyticsDecisionWorkspace } from "../../api/generated/dekopen";
import type {
  AnalyticsWorkspace,
  AnalyticsMetric,
  AnalyticsDetail,
} from "../../api/generated/models";
import { apiFetchBlob, ApiError } from "../../api/apiMutator";
import { useAuthSession } from "../../auth/AuthSessionProvider";
import { actionErrorDetail } from "../errors";
import {
  Button,
  DataTable,
  DateOnly,
  DemoBadge,
  Dialog,
  DeniedState,
  EmptyState,
  ErrorState,
  LoadingState,
  Money,
  Percent,
  Qty,
  Tabs,
  ValidatedForm,
} from "../../ui";
import { CostClosure } from "./CostClosure";
import { driverLabels, type Work } from "./types";
import "./analytics.css";

const questions = {
  sales: "¿Cuánto de lo que cotizas se aprueba?",
  margin: "¿Ganas lo que cotizaste en cada obra?",
  production: "¿Dónde se pierde material o tiempo?",
  field: "¿Se cumple lo prometido en obra?",
};
const sources = {
  sales: "Revisiones emitidas y decisiones del cliente.",
  margin: "Revisión elegida, consumos de inventario y cierres de costos.",
  production: "Plan de corte, inventario físico y eventos de estación.",
  field: "Agenda, actas firmadas e incidencias de terreno.",
};
type Group = keyof typeof questions;

export function AnalyticValue({
  value,
  unit,
  currency,
}: {
  value: string | null;
  unit: string;
  currency?: string | null;
}): JSX.Element {
  if (value === null) return <span>Sin datos suficientes</span>;
  if (unit === "money") return <Money value={value} currency={currency ?? "CLP"} />;
  if (unit === "fraction") return <Percent value={value} kind="fraction" />;
  return (
    <Qty value={value} precision={unit === "hours" ? 2 : 0} unit={unit === "hours" ? "h" : "un."} />
  );
}

function Reading({
  metric,
  onOpen,
}: {
  metric: AnalyticsMetric;
  onOpen: (metric: AnalyticsMetric) => void;
}): JSX.Element {
  return (
    <div className="analytics-reading">
      <div>
        <h3>{metric.label}</h3>
        <p>{metric.value === null ? metric.reason : sources[metric.group as Group]}</p>
      </div>
      <div className="analytics-reading__value">
        <button
          className="analytics-number"
          data-metric={metric.key}
          onClick={() => onOpen(metric)}
          aria-label={`${metric.label}: ver fuente`}
        >
          <AnalyticValue value={metric.value} unit={metric.unit} currency={metric.currency} />
        </button>
        <Button onClick={() => onOpen(metric)}>¿Cómo se calcula?</Button>
      </div>
    </div>
  );
}

function MetricDefinition({
  metric,
  onClose,
  onOpenOrder,
}: {
  metric: AnalyticsMetric;
  onClose: () => void;
  onOpenOrder: (id: string, movement?: string) => void;
}): JSX.Element {
  return (
    <Dialog title={metric.label} width="l" onClose={onClose}>
      <p>{metric.formula}</p>
      <p>{sources[metric.group as Group]}</p>
      {metric.reason && <p role="status">Sin datos suficientes · {metric.reason}</p>}
      <p>
        <AnalyticValue value={metric.value} unit={metric.unit} currency={metric.currency} />
      </p>
      <DataTable<AnalyticsDetail & { row_index: number }>
        rows={metric.details.map((row, row_index) => ({ ...row, row_index }))}
        rowKey={(r) => String(r.row_index)}
        label="Obras y registros de esta cifra"
        emptyReason="No hay registros que compongan esta cifra."
        columns={[
          {
            id: "code",
            label: "Origen",
            value: (r) => r.code,
            render: (r) =>
              r.href.startsWith("/analytics?order=") ? (
                <Button
                  onClick={() =>
                    onOpenOrder(
                      new URLSearchParams(r.href.split("?")[1]).get("order")!,
                      new URLSearchParams(r.href.split("?")[1]).get("movement") ?? undefined,
                    )
                  }
                >
                  {r.code} · Ver movimiento
                </Button>
              ) : (
                <Link to={r.href}>{r.code}</Link>
              ),
          },
          {
            id: "label",
            label: "Evidencia",
            value: (r) => r.label,
            render: (r) => (
              <span>
                {r.label}
                {r.reason && <small>{r.reason}</small>}
              </span>
            ),
          },
          {
            id: "value",
            label: "Valor",
            value: (r) => r.value,
            numeric: true,
            render: (r) => <AnalyticValue value={r.value} unit={r.unit} currency={r.currency} />,
          },
        ]}
      />
      <details>
        <summary>Detalles técnicos de la definición</summary>
        <p>{metric.source}</p>
      </details>
    </Dialog>
  );
}

function MarginChart({ work, onOpen }: { work: Work; onOpen: (key: string) => void }): JSX.Element {
  return (
    <figure className="analytics-figure" aria-label={`Margen de ${work.code}`}>
      <figcaption>
        {work.code} · {work.name} {work.demo && <DemoBadge />}
      </figcaption>
      {[
        { label: "Cotizado", value: work.quoted_margin },
        { label: "Real", value: work.real_margin },
      ].map((line) => (
        <div className="analytics-bar" key={line.label}>
          <span>{line.label}</span>
          <span className="analytics-bar__track" aria-hidden>
            <span
              style={{ width: `${Math.min(100, Math.abs(Number(line.value ?? 0)) * 100)}%` }}
              data-negative={Number(line.value) < 0}
            />
          </span>
          <button
            className="analytics-number"
            data-metric={`${line.label === "Real" ? "real" : "quoted"}_margin`}
            onClick={() => onOpen(line.label === "Real" ? "real_margin" : "quoted_margin")}
            aria-label={`${line.label}: ver fuente`}
          >
            <Percent
              value={line.value}
              kind="fraction"
              cause={work.reason ?? "Falta cierre de costos"}
            />
          </button>
        </div>
      ))}
      <p>
        Revisión {work.revision} elegida y costo de todas sus OT. El ancho de la barra compara el
        margen; la cifra conserva su signo.
      </p>
    </figure>
  );
}

function DecisionChart({
  title,
  items,
  onOpen,
}: {
  title: string;
  items: AnalyticsMetric[];
  onOpen: (metric: AnalyticsMetric) => void;
}): JSX.Element | null {
  const measured = items.filter((m) => m.value !== null);
  if (!measured.length) return null;
  const ceiling = Math.max(...measured.map((m) => (m.unit === "fraction" ? 1 : Number(m.value))));
  return (
    <figure className="analytics-figure">
      <figcaption>{title}</figcaption>
      {measured.map((m) => (
        <div className="analytics-bar analytics-bar--decision" key={m.key}>
          <span>{m.label}</span>
          <span className="analytics-bar__track" aria-hidden>
            <span
              style={{
                width: `${ceiling ? Math.min(100, (Math.abs(Number(m.value)) / ceiling) * 100) : 0}%`,
              }}
            />
          </span>
          <button
            className="analytics-number"
            data-metric={m.key}
            onClick={() => onOpen(m)}
            aria-label={`${m.label}: ver fuente`}
          >
            <AnalyticValue value={m.value} unit={m.unit} currency={m.currency} />
          </button>
        </div>
      ))}
      <p>
        {sources[measured[0]!.group as Group]}{" "}
        {measured.length < items.length && "Hay lecturas incompletas; revisa sus causas debajo."}
      </p>
    </figure>
  );
}

export function AnalyticsPage(): JSX.Element {
  const orgId = useAuthSession().me?.active_organization?.id;
  return <AnalyticsWorkspace key={orgId} />;
}

function AnalyticsWorkspace(): JSX.Element {
  const auth = useAuthSession();
  const org = auth.me?.active_organization;
  const allowed = org?.role === "OWNER" || org?.role === "WORKSHOP_MANAGER";
  const [params, setParams] = useSearchParams();
  const initial = params.get("view");
  const group: Group = initial && initial in questions ? (initial as Group) : "margin";
  const [data, setData] = useState<AnalyticsWorkspace>();
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [denied, setDenied] = useState(false);
  const [definition, setDefinition] = useState<AnalyticsMetric>();
  const [selected, setSelected] = useState<Work>();
  const [order, setOrder] = useState<string>();
  const [movement, setMovement] = useState<string>();
  const [exporting, setExporting] = useState(false);
  const readSerial = useRef(0);
  const load = useCallback(
    async (dates?: { start: string; end: string }) => {
      const serial = ++readSerial.current;
      if (!allowed) return;
      setLoading(true);
      setError("");
      setDenied(false);
      setSelected(undefined);
      try {
        const response = await analyticsDecisionWorkspace(dates);
        if (serial !== readSerial.current) return;
        if (!("metrics" in response.data)) throw new Error("analytics_response");
        setData(response.data);
        setStart(response.data.start);
        setEnd(response.data.end);
      } catch (e) {
        if (serial !== readSerial.current) return;
        if (e instanceof ApiError && e.status === 403) setDenied(true);
        else
          setError(
            actionErrorDetail(
              e,
              "No pudimos calcular la analítica. Revisa la conexión y vuelve a intentar.",
            ),
          );
      } finally {
        if (serial === readSerial.current) setLoading(false);
      }
    },
    [allowed, org?.id],
  );
  useEffect(() => {
    setData(undefined);
    setDefinition(undefined);
    setOrder(undefined);
    void load();
    return () => {
      readSerial.current += 1;
    };
  }, [load]);
  useEffect(() => {
    const key = params.get("definition");
    if (key && data) {
      const found = data.metrics.find((m) => m.key === key || m.key.split(":")[0] === key);
      if (found) setDefinition(found);
    }
    if (params.get("order")) setOrder(params.get("order")!);
  }, [data, params]);
  useLayoutEffect(() => {
    const handle = (event: KeyboardEvent) => {
      if (event.key !== "F6" || definition || order) return;
      const button = (document.activeElement as HTMLElement)?.closest<HTMLElement>("[data-metric]");
      const found =
        data?.metrics.find(
          (m) =>
            m.key === button?.dataset.metric ||
            (m.key.startsWith(`${button?.dataset.metric}:`) &&
              m.label.endsWith(
                `· ${button?.dataset.work ?? (selected ?? (data?.works[0] as unknown as Work))?.code}`,
              )),
        ) ?? data?.metrics.find((m) => m.group === group);
      if (found) {
        event.preventDefault();
        setDefinition(found);
      }
    };
    window.addEventListener("keydown", handle);
    return () => window.removeEventListener("keydown", handle);
  }, [data, group, definition, order, selected]);
  if (!allowed || denied)
    return (
      <section data-density="office">
        <h1>Analítica</h1>
        <DeniedState reason="El dueño y el jefe de taller pueden leer costos y analítica. Pide ese permiso al dueño de tu organización." />
      </section>
    );
  const works = (data?.works ?? []) as unknown as Work[];
  const activeWork = selected ?? works[0];
  const visible = (data?.metrics ?? []).filter((m) => m.group === group && !(group === "margin"));
  async function download() {
    setExporting(true);
    setError("");
    try {
      const { blob, filename } = await apiFetchBlob(
        `/api/v1/analytics/decision/export/?${new URLSearchParams({ start, end })}`,
      );
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename ?? `analitica-${start}-${end}.csv`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setError(actionErrorDetail(e, "No pudimos exportar el detalle."));
    } finally {
      setExporting(false);
    }
  }
  const openWorkMetric = (work: Work, key: string) => {
    const found = data?.metrics.find(
      (m) =>
        m.key.startsWith(`${key}:`) &&
        (m.label.endsWith(`· ${work.code}`) || m.details.some((d) => d.code === work.code)),
    );
    if (found) setDefinition(found);
  };
  return (
    <section className="analytics-page" data-density="office">
      <header>
        <div>
          <h1>Analítica</h1>
          <p>Decide con la revisión y el registro que respaldan cada cifra.</p>
        </div>
        <Button loading={exporting} disabled={!data || loading} onClick={() => void download()}>
          Exportar detalle CSV
        </Button>
      </header>
      <ValidatedForm
        className="analytics-period"
        onSubmit={(e) => {
          e.preventDefault();
          void load({ start, end });
        }}
      >
        <label>
          Desde
          <input
            type="date"
            className="ui-field__input"
            required
            disabled={loading}
            value={start}
            onChange={(e) => setStart(e.target.value)}
          />
        </label>
        <label>
          Hasta
          <input
            type="date"
            className="ui-field__input"
            required
            disabled={loading}
            value={end}
            onChange={(e) => setEnd(e.target.value)}
          />
        </label>
        <Button type="submit" variant="primary" loading={loading}>
          Aplicar período
        </Button>
      </ValidatedForm>
      <Tabs
        label="Preguntas para decidir"
        value={group}
        items={Object.keys(questions).map((id) => ({
          id,
          label:
            { sales: "Ventas", margin: "Margen", production: "Producción", field: "Terreno" }[id] ??
            id,
        }))}
        onChange={(id) => {
          const next = new URLSearchParams(params);
          next.set("view", id);
          next.delete("definition");
          setParams(next);
          setSelected(undefined);
        }}
      />
      <h2>{questions[group]}</h2>
      <p className="analytics-source">
        {sources[group]}{" "}
        {data && (
          <>
            Emisión/liberación o agenda desde <DateOnly value={data.start} /> hasta{" "}
            <DateOnly value={data.end} />; decisiones y estados al consultar.
          </>
        )}
      </p>
      {error && (
        <ErrorState
          body={error}
          onRetry={() => void load(start && end ? { start, end } : undefined)}
        />
      )}
      {loading ? (
        <LoadingState label="Calculando desde los registros de tu organización" />
      ) : data === undefined ? null : data.empty ? (
        <EmptyState
          title="Todavía no hay registros en este período"
          body="Emite una cotización o elige otro período para analizarla."
          action={
            <Link className="ui-button" to="/projects">
              Abrir proyectos
            </Link>
          }
        />
      ) : (
        <>
          {group === "margin" && (
            <>
              {!works.length ? (
                <EmptyState
                  title="No hay una revisión aprobada en esta cohorte"
                  body="El margen se compara con la solución elegida por el cliente. Revisa sus decisiones en Cotizaciones."
                  action={
                    <Link className="ui-button" to="/quotes">
                      Abrir cotizaciones
                    </Link>
                  }
                />
              ) : (
                <>
                  <DataTable<Work>
                    label="Margen por obra"
                    rows={works}
                    rowKey={(w) => w.id}
                    emptyReason="No hay obras aprobadas en este período."
                    columns={[
                      {
                        id: "code",
                        label: "Obra",
                        value: (w) => w.code,
                        render: (w) => (
                          <button className="analytics-entity" onClick={() => setSelected(w)}>
                            {w.code} · {w.name}
                            {w.demo && <DemoBadge />}
                          </button>
                        ),
                      },
                      {
                        id: "quoted_margin",
                        label: "Cotizado",
                        numeric: true,
                        value: (w) => w.quoted_margin,
                        render: (w) => (
                          <button
                            className="analytics-number"
                            data-metric="quoted_margin"
                            data-work={w.code}
                            onClick={() => openWorkMetric(w, "quoted_margin")}
                          >
                            <Percent value={w.quoted_margin} kind="fraction" />
                          </button>
                        ),
                      },
                      {
                        id: "real_margin",
                        label: "Real",
                        numeric: true,
                        value: (w) => w.real_margin,
                        render: (w) => (
                          <button
                            className="analytics-number"
                            data-metric="real_margin"
                            data-work={w.code}
                            onClick={() => openWorkMetric(w, "real_margin")}
                          >
                            <AnalyticValue value={w.real_margin} unit="fraction" />
                            {w.reason && (
                              <small className="analytics-reason" title={w.reason}>
                                Ver qué falta
                              </small>
                            )}
                          </button>
                        ),
                      },
                      {
                        id: "delta",
                        label: "Desvío de utilidad",
                        numeric: true,
                        value: (w) => w.delta_profit,
                        render: (w) => (
                          <button
                            className="analytics-number"
                            data-metric="delta_profit"
                            data-work={w.code}
                            onClick={() => openWorkMetric(w, "delta_profit")}
                          >
                            <AnalyticValue
                              value={w.delta_profit}
                              unit="money"
                              currency={w.currency}
                            />
                          </button>
                        ),
                      },
                    ]}
                  />
                  {activeWork && (
                    <div className="analytics-work">
                      <MarginChart
                        work={activeWork}
                        onOpen={(key) => openWorkMetric(activeWork, key)}
                      />
                      <WorkCauses
                        work={activeWork}
                        onOpenOrder={setOrder}
                        onDriver={(key) => openWorkMetric(activeWork, `driver_${key}`)}
                      />
                    </div>
                  )}
                  <details>
                    <summary>Desvío por tipología</summary>
                    {data?.metrics
                      .filter((m) => m.key.startsWith("deviation_typology:"))
                      .map((m) => (
                        <Reading key={m.key} metric={m} onOpen={setDefinition} />
                      ))}
                  </details>
                </>
              )}
            </>
          )}
          {group !== "margin" && (
            <div className="analytics-readings">
              {group === "sales" && (
                <DecisionChart
                  title="¿Cómo cambia la conversión por estimador?"
                  items={visible.filter((m) => m.key.startsWith("conversion_estimator:"))}
                  onOpen={setDefinition}
                />
              )}
              {group === "production" && (
                <DecisionChart
                  title="¿La pérdida real coincide con el plan?"
                  items={visible.filter((m) => ["planned_waste", "actual_waste"].includes(m.key))}
                  onOpen={setDefinition}
                />
              )}
              {group === "production" && (
                <DecisionChart
                  title="¿Qué estación ocupa más tiempo transcurrido?"
                  items={visible.filter((m) => m.key.startsWith("station_time:"))}
                  onOpen={setDefinition}
                />
              )}
              {visible.map((m) => (
                <Reading key={m.key} metric={m} onOpen={setDefinition} />
              ))}
            </div>
          )}
        </>
      )}
      {definition && (
        <MetricDefinition
          metric={definition}
          onOpenOrder={(id, origin) => {
            setDefinition(undefined);
            if (params.has("definition")) {
              const next = new URLSearchParams(params);
              next.delete("definition");
              setParams(next);
            }
            setMovement(origin);
            setOrder(id);
          }}
          onClose={() => {
            setDefinition(undefined);
            if (params.has("definition")) {
              const next = new URLSearchParams(params);
              next.delete("definition");
              setParams(next);
            }
          }}
        />
      )}
      {order && (
        <CostClosure
          orderId={order}
          focusId={movement ?? params.get("movement") ?? undefined}
          onClose={() => {
            setOrder(undefined);
            setMovement(undefined);
            if (params.has("order")) {
              const next = new URLSearchParams(params);
              next.delete("order");
              next.delete("movement");
              setParams(next);
            }
          }}
          onSaved={() => {
            setOrder(undefined);
            setMovement(undefined);
            if (params.has("order")) {
              const next = new URLSearchParams(params);
              next.delete("order");
              next.delete("movement");
              setParams(next);
            }
            void load({ start, end });
          }}
        />
      )}
    </section>
  );
}

function WorkCauses({
  work,
  onOpenOrder,
  onDriver,
}: {
  work: Work;
  onOpenOrder: (id: string) => void;
  onDriver: (key: string) => void;
}): JSX.Element {
  return (
    <section className="analytics-causes">
      <h3>¿Por qué cambió la utilidad?</h3>
      {work.reason ? (
        <p>Sin datos suficientes · {work.reason}</p>
      ) : (
        <>
          <dl>
            {work.drivers.map((d) => (
              <div key={d.key}>
                <dt>{driverLabels[d.key]}</dt>
                <dd>
                  <button
                    className="analytics-number"
                    data-metric={`driver_${d.key}`}
                    onClick={() => onDriver(d.key)}
                    aria-label={`${driverLabels[d.key]}: ver movimientos`}
                  >
                    <Money value={d.amount} currency={work.currency} />
                  </button>
                </dd>
              </div>
            ))}
          </dl>
          <p>
            Descuento de la revisión elegida:{" "}
            <button
              className="analytics-number"
              data-metric="driver_discount"
              onClick={() => onDriver("discount")}
              aria-label="Descuento: ver revisión elegida"
            >
              <Money value={work.discount} currency={work.currency} />
            </button>
            . Ya está incluido en el margen cotizado; no se vuelve a restar.
          </p>
        </>
      )}
      <ul>
        {work.orders.map((o) => (
          <li key={o.id}>
            <div>
              <Link to={o.href}>
                {o.code}
                {o.remake ? " · Reposición" : ""}
              </Link>
              <small>{o.source}</small>
            </div>
            <Button onClick={() => onOpenOrder(o.id)}>Ver consumos y costos</Button>
          </li>
        ))}
      </ul>
      <Link to={`/projects/${work.id}?section=quote`}>Abrir revisión elegida</Link>
    </section>
  );
}
