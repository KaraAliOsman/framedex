import { useState } from "react";
import { Link } from "react-router-dom";
import type { TodayAction } from "../api/generated/models";
import { useAuthSession } from "../auth/AuthSessionProvider";
import { DateOnly, DeniedState, ErrorState, LoadingState, Money, PageHeader } from "../ui";
import { PriceDecision } from "../features/pricing/PriceDecision";
import { CollectionReminder } from "../features/projects/CollectionReminder";
import { useToday } from "./useToday";
import { consequenceLabels, phaseLabels } from "./todayLabels";

export function DashboardPage(): JSX.Element {
  const auth = useAuthSession();
  const org = auth.me?.active_organization;
  if (!org) return <DeniedState reason="Selecciona una organización para ver tu trabajo de hoy." />;
  return <TodayWorkspace key={[org.id, auth.me?.user.id, org.role].join(":")} />;
}

function TodayWorkspace(): JSX.Element {
  const org = useAuthSession().me!.active_organization!;
  const query = useToday();
  const [decision, setDecision] = useState<TodayAction | null>(null);
  const [tier, setTier] = useState("");
  const [page, setPage] = useState(0);
  const actions = (query.data?.actions ?? []).filter((item) => !tier || item.consequence === tier);
  const currentPage = Math.min(page, Math.max(0, Math.ceil(actions.length / 50) - 1));
  const visible = actions.slice(currentPage * 50, (currentPage + 1) * 50);
  const tiers = [...new Set(query.data?.actions.map((item) => item.consequence) ?? [])];
  const workshop =
    org.role === "INSTALLER" || org.role === "OPERATOR" || org.role === "WORKSHOP_MANAGER";
  return (
    <section className="today-page" aria-labelledby="page-title">
      <PageHeader
        title="Hoy"
        headingId="page-title"
        context={org.name}
        actions={
          <Link className="ui-button" to={workshop ? "/production" : "/projects"}>
            {org.role === "INSTALLER"
              ? "Abrir despachos e instalaciones"
              : workshop
                ? "Abrir taller"
                : "Abrir proyectos"}
          </Link>
        }
      />
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
          <p className="today-date">
            <DateOnly value={query.data.today} /> ·{" "}
            {org.role === "INSTALLER"
              ? "Entregas e instalaciones comprometidas"
              : "Primero lo vencido y lo que bloquea a otros"}
          </p>
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
          {query.data.actions.length === 0 ? (
            <div className="today-clear">
              <h2>Todo al día</h2>
              <p>No hay compromisos pendientes para tu rol en esta organización.</p>
            </div>
          ) : (
            <>
              <nav className="today-filters" aria-label="Filtrar por consecuencia">
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
                        <h2>{item.title}</h2>
                        <p>{item.entity_name}</p>
                        <p>{item.reason}</p>
                        {item.key.startsWith("receivable_overdue:") && org.role === "OWNER" && (
                          <CollectionReminder
                            orgId={org.id}
                            projectId={item.key.slice("receivable_overdue:".length)}
                          />
                        )}
                        {item.amount !== null && item.currency && (
                          <p className="today-amount">
                            <Money value={item.amount} currency={item.currency} />
                          </p>
                        )}
                        {item.source && (
                          <details className="today-source">
                            <summary>¿De dónde sale?</summary>
                            <p>{item.source}</p>
                            {item.balance_total !== null && item.currency && (
                              <dl>
                                <dt>Total sellado</dt>
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
            <section className="today-pipeline" aria-label="Venta por fase">
              <h2>Venta por fase</h2>
              <p>Totales emitidos, separados por moneda.</p>
              <ul>
                {query.data.pipeline.map((item) => (
                  <li key={`${item.phase}:${item.currency}`}>
                    <Link to={item.href}>
                      <span>{phaseLabels[item.phase] ?? "Fase sin dato"}</span>
                      <span className="ui-value">
                        {item.count} {item.count === 1 ? "proyecto" : "proyectos"}
                      </span>
                      {item.currency ? (
                        <Money
                          value={item.amount}
                          currency={item.currency}
                          cause="Falta el total sellado"
                        />
                      ) : (
                        <span>Sin dato · falta moneda sellada</span>
                      )}
                    </Link>
                    {item.unknown_count > 0 && (
                      <p>
                        <span className="ui-value">{item.unknown_count}</span> sin total o moneda
                        sellada · <Link to={item.href}>Revisar</Link>
                      </p>
                    )}
                    <details className="today-source">
                      <summary>¿De dónde sale?</summary>
                      <p>{item.source}</p>
                    </details>
                  </li>
                ))}
              </ul>
            </section>
          )}
        </>
      )}
    </section>
  );
}
