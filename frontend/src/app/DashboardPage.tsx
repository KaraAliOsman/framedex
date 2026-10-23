import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { catalogSystemList } from "../api/generated/dekopen";
import type { TodayAction } from "../api/generated/models";
import { useAuthSession } from "../auth/AuthSessionProvider";
import {
  Button,
  DateOnly,
  DeniedState,
  Dialog,
  ErrorState,
  Icon,
  LoadingState,
  Money,
} from "../ui";
import { PriceDecision } from "../features/pricing/PriceDecision";
import { CollectionReminder } from "../features/projects/CollectionReminder";
import { useToday } from "./useToday";
import { consequenceLabels, phaseLabels } from "./todayLabels";
import { SourceSummary } from "../ui/SourceSummary";
import { useNewQuotation } from "../features/projects/useNewQuotation";
import { todayDate, todayGreeting, todayMetrics } from "./todaySummary";

export function DashboardPage(): JSX.Element {
  const auth = useAuthSession();
  const org = auth.me?.active_organization;
  if (!org) return <DeniedState reason="Selecciona una organización para ver tu trabajo de hoy." />;
  return <TodayWorkspace key={[org.id, auth.me?.user?.id, org.role].join(":")} />;
}

function TodayWorkspace(): JSX.Element {
  const auth = useAuthSession();
  const org = auth.me!.active_organization!;
  const query = useToday();
  const { creating, createError, startQuotation } = useNewQuotation(org.id);
  const [reviewPrepared, setReviewPrepared] = useState(false);
  const [decision, setDecision] = useState<TodayAction | null>(null);
  const [tier, setTier] = useState("");
  const [page, setPage] = useState(0);
  const actions = (query.data?.actions ?? []).filter((item) => !tier || item.consequence === tier);
  const currentPage = Math.min(page, Math.max(0, Math.ceil(actions.length / 50) - 1));
  const visible = actions.slice(currentPage * 50, (currentPage + 1) * 50);
  const tiers = [...new Set(query.data?.actions.map((item) => item.consequence) ?? [])];
  const workshop =
    org.role === "INSTALLER" || org.role === "OPERATOR" || org.role === "WORKSHOP_MANAGER";
  const prepared = query.data?.prepared;
  // A workshop without its own series is on first use: Hoy points to the guide.
  const ownSeries = useQuery({
    queryKey: ["today-own-series", org.id],
    enabled: !workshop && query.data?.actions.length === 0,
    staleTime: 60_000,
    queryFn: async ({ signal }) => {
      const response = await catalogSystemList(
        { summary: true, is_demo: false, owned_only: true },
        { headers: { "X-Organization-ID": org.id }, signal },
      );
      if (response.status !== 200) throw new Error("catalog");
      return response.data.items.length;
    },
  });
  const metrics = todayMetrics(query.data?.actions ?? [], org.role);
  const name =
    auth.session?.user.user_metadata?.full_name ?? auth.session?.user.user_metadata?.name;
  return (
    <section className="today-page" aria-labelledby="page-title">
      <header className="today-head">
        <div>
          <p className="today-date">
            {query.data && <time dateTime={query.data.today}>{todayDate(query.data.today)}</time>}
          </p>
          <h1 id="page-title">{todayGreeting(name)}</h1>
        </div>
        {workshop ? (
          <Link
            className="ui-button ui-button--primary"
            to={org.role === "INSTALLER" ? "/field" : "/production"}
          >
            {org.role === "INSTALLER" ? "Abrir instalaciones" : "Abrir taller"}
          </Link>
        ) : (
          <Button
            // On first use «Empezar» is the one primary action of the page.
            variant={ownSeries.data === 0 ? "secondary" : "primary"}
            loading={creating}
            onClick={() => void startQuotation()}
            icon={<Icon name="plus" />}
          >
            Nueva cotización
          </Button>
        )}
      </header>
      {createError && <p role="alert">{createError}</p>}
      {query.isPending ? (
        <LoadingState label="Consultando los compromisos de hoy" />
      ) : query.isError ? (
        <ErrorState
          title="No se pudo consultar tu trabajo"
          body="Los compromisos se conservan. Reintenta para ver la cola vigente de tu organización."
          onRetry={() => void query.refetch()}
        />
      ) : (
        <>
          {metrics.length > 0 && (
            <section className="today-metrics" aria-label="Resumen de hoy">
              {metrics.map((metric) => (
                <div key={metric.label} data-tier={metric.tier}>
                  <span>{metric.label}</span>
                  <strong className="ui-value">{metric.count}</strong>
                </div>
              ))}
            </section>
          )}
          {prepared && prepared.count > 0 && (
            <section className="today-prepared" aria-labelledby="prepared-title">
              <span className="today-prepared__icon" aria-hidden="true">
                <Icon name="check" size={20} />
              </span>
              <div>
                <h2 id="prepared-title">
                  DEKOPEN preparó {prepared.count} {prepared.count === 1 ? "cosa" : "cosas"}
                </h2>
                <p>
                  {prepared.count === 1
                    ? "Una cotización guardada por tu asistente."
                    : "Cotizaciones guardadas por tu asistente."}
                </p>
              </div>
              <Button onClick={() => setReviewPrepared(true)}>Revisar</Button>
            </section>
          )}
          {reviewPrepared && prepared && (
            <Dialog title="Cotizaciones preparadas" onClose={() => setReviewPrepared(false)}>
              <ul className="today-prepared__list">
                {prepared.items.map((item) => (
                  <li key={item.project_id}>
                    <Link to={item.href}>
                      <strong>{item.name}</strong>
                      <span>{item.code}</span>
                    </Link>
                  </li>
                ))}
              </ul>
              {prepared.count > prepared.items.length && (
                <Link to="/projects">Ver todas las obras</Link>
              )}
            </Dialog>
          )}
          {decision?.operation_id && (
            <section className="today-decision" aria-label="Decisión de precio">
              <div className="today-decision__head">
                <h2>
                  {decision.entity_code} · {decision.title}
                </h2>
                <button type="button" onClick={() => setDecision(null)}>
                  Cerrar revisión
                </button>
              </div>
              <PriceDecision
                key={decision.operation_id}
                operationId={decision.operation_id}
                owner={org.role === "OWNER"}
              />
            </section>
          )}
          {query.data.actions.length === 0 && ownSeries.data === 0 ? (
            <div className="today-clear today-first-use">
              <h2>Prepara tu taller</h2>
              <p>
                Elige tu serie del fabricante, carga sus perfiles y precios, comprueba una ventana y
                envía tu primera cotización.
              </p>
              <Link className="ui-button ui-button--primary" to="/onboarding">
                Empezar
              </Link>
            </div>
          ) : query.data.actions.length === 0 ? (
            <div className="today-clear">
              <h2>Todo al día</h2>
              <p>No hay compromisos pendientes para tu rol en esta organización.</p>
            </div>
          ) : (
            <>
              <h2 className="today-section-title">Para hacer</h2>
              <nav className="today-filters ui-segmented" aria-label="Filtrar por consecuencia">
                <button
                  type="button"
                  aria-pressed={!tier}
                  onClick={() => {
                    setTier("");
                    setPage(0);
                  }}
                >
                  Todo
                </button>
                {tiers.map((value) => (
                  <button
                    key={value}
                    type="button"
                    aria-pressed={tier === value}
                    onClick={() => {
                      setTier(value);
                      setPage(0);
                    }}
                  >
                    {consequenceLabels[value] ?? "Por revisar"}
                  </button>
                ))}
              </nav>
              {actions.length === 0 ? (
                <p>
                  No quedan acciones con este filtro.{" "}
                  <button type="button" onClick={() => setTier("")}>
                    Ver toda la cola
                  </button>
                </p>
              ) : (
                <ol className="today-queue" aria-label="Acciones pendientes">
                  {visible.map((item) => (
                    <li key={item.key} className="today-action" data-consequence={item.consequence}>
                      <div className="today-action__context">
                        <span className="today-tier">
                          {consequenceLabels[item.consequence] ?? "Por revisar"}
                        </span>
                        <span className="ui-value today-code">{item.entity_code}</span>
                        {item.due_on && <DateOnly value={item.due_on} />}
                      </div>
                      <div className="today-action__body">
                        <h3>{item.title}</h3>
                        <p>{item.entity_name}</p>
                        {item.amount !== null && item.currency && (
                          <p className="today-amount">
                            <Money value={item.amount} currency={item.currency} />
                          </p>
                        )}
                        {(item.source || item.reason) && (
                          <details className="today-source">
                            <SourceSummary />
                            <p>{item.reason}</p>
                            <p>{item.source}</p>
                            {item.key.startsWith("receivable_overdue:") && org.role === "OWNER" && (
                              <CollectionReminder
                                orgId={org.id}
                                projectId={item.key.slice("receivable_overdue:".length)}
                              />
                            )}
                            {item.balance_total !== null && item.currency && (
                              <dl>
                                <dt>Total emitido</dt>
                                <dd>
                                  <Money value={item.balance_total} currency={item.currency} />
                                </dd>
                                <dt>Pagos vigentes</dt>
                                <dd>
                                  <Money value={item.balance_collected} currency={item.currency} />
                                </dd>
                              </dl>
                            )}
                          </details>
                        )}
                      </div>
                      {item.operation_id ? (
                        <button
                          type="button"
                          className="ui-button today-verb"
                          onClick={() => setDecision(item)}
                          aria-expanded={decision?.key === item.key}
                        >
                          {item.verb}
                        </button>
                      ) : (
                        <Link className="ui-button today-verb" to={item.href}>
                          {item.verb}
                        </Link>
                      )}
                    </li>
                  ))}
                </ol>
              )}
              {actions.length > 50 && (
                <nav className="today-pagination" aria-label="Páginas de acciones">
                  <button
                    type="button"
                    disabled={currentPage === 0}
                    onClick={() => setPage(currentPage - 1)}
                  >
                    Anterior
                  </button>
                  <span className="ui-value">
                    {currentPage * 50 + 1}–{Math.min((currentPage + 1) * 50, actions.length)} de{" "}
                    {actions.length} acciones
                  </span>
                  <button
                    type="button"
                    disabled={(currentPage + 1) * 50 >= actions.length}
                    onClick={() => setPage(currentPage + 1)}
                  >
                    Siguiente
                  </button>
                </nav>
              )}
            </>
          )}
          {query.data.pipeline.length > 0 && (
            <details className="today-pipeline" aria-label="Venta por etapa">
              <summary>Venta por etapa</summary>
              <p>Totales emitidos, separados por moneda.</p>
              <ul>
                {query.data.pipeline.map((item) => (
                  <li key={`${item.phase}:${item.currency}`}>
                    <Link to={item.href}>
                      <span>{phaseLabels[item.phase] ?? "Revisar etapa"}</span>
                      <span className="ui-value">
                        {item.count} {item.count === 1 ? "obra" : "obras"}
                      </span>
                      {item.currency ? (
                        <Money
                          value={item.amount}
                          currency={item.currency}
                          cause="Falta el total emitido"
                        />
                      ) : (
                        <span>Falta moneda · Revisar cotización</span>
                      )}
                    </Link>
                    {item.unknown_count > 0 && (
                      <p>
                        <span className="ui-value">{item.unknown_count}</span> sin total o moneda de
                        emisión · <Link to={item.href}>Revisar</Link>
                      </p>
                    )}
                    <details className="today-source">
                      <SourceSummary />
                      <p>{item.source}</p>
                    </details>
                  </li>
                ))}
              </ul>
            </details>
          )}
        </>
      )}
    </section>
  );
}
