import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link, useSearchParams } from "react-router-dom";

import { ApiError } from "../../api/apiMutator";
import { engineSystems } from "../../api/generated/dekopen";
import type { ProjectResponse, TodayAction } from "../../api/generated/models";
import { useToday } from "../../app/useToday";
import { formatRelativeTimestamp } from "../../decimal";
import { formatDateTime } from "../../format";
import { t, type TranslationKey } from "../../i18n/es-CL";
import { Button, EmptyState } from "../../ui";
import { Icon } from "../../ui/Icon";
import { StatusBadge } from "../../ui/StatusBadge";
import { formatMoney } from "../money";
import "./projects-home.css";
import { useNewQuotation } from "./useNewQuotation";
export { draftQuotationName } from "./useNewQuotation";

export const PROJECT_STATUS: Record<ProjectResponse["status"], TranslationKey> = {
  DRAFT: "projects.draft",
  QUOTED: "projects.quoted",
  APPROVED: "projects.approved",
  IN_PRODUCTION: "projects.production",
  COMPLETED: "projects.completed",
  CANCELLED: "projects.cancelled",
};

const FILTERS: { value: string; label: string }[] = [
  { value: "", label: "Todos" },
  { value: "DRAFT", label: "Borradores" },
  { value: "QUOTED", label: "Cotizados" },
  { value: "APPROVED", label: "Aprobados" },
  { value: "IN_PRODUCTION", label: "En producción" },
  { value: "COMPLETED", label: "Terminados" },
];

/** «¿Con qué obra continúo o cómo empiezo otra?» (screen contract: Proyectos).
 * One click starts a draft quotation and opens the typology library; the
 * client is added when it is needed, never before the first window. */
export function ProjectsHome({
  items,
  orgId,
  orgName,
  canWrite,
}: {
  items: ProjectResponse[];
  orgId: string;
  orgName: string;
  canWrite: boolean;
}): JSX.Element {
  const [params, setParams] = useSearchParams();
  const { creating, createError, startQuotation } = useNewQuotation(orgId);

  const search = params.get("q") ?? "";
  const statusFilter = params.get("status") ?? "";
  const sortKey = params.get("sort") ?? "updated";
  function setParam(key: string, value: string, fallback = ""): void {
    setParams(
      (current) => {
        const next = new URLSearchParams(current);
        if (value && value !== fallback) next.set(key, value);
        else next.delete(key);
        return next;
      },
      { replace: true },
    );
  }

  const systems = useQuery({
    queryKey: ["project-systems", orgId],
    queryFn: async () => {
      const response = await engineSystems({ headers: { "X-Organization-ID": orgId } });
      if (response.status !== 200) throw new ApiError(response.status, response.data);
      return response.data.systems;
    },
    retry: false,
    staleTime: 60_000,
  });
  const noSystems = systems.isSuccess && systems.data.length === 0;

  const today = useToday();
  const decisions = useMemo(() => groupDecisions(today.data?.actions ?? []), [today.data]);

  const needle = search.toLocaleLowerCase("es-CL");
  const visible = items
    .filter(
      (item) =>
        (statusFilter === "" || item.status === statusFilter) &&
        `${item.code} ${item.name} ${item.client_name}`.toLocaleLowerCase("es-CL").includes(needle),
    )
    .sort((a, b) =>
      sortKey === "name"
        ? (a.name || a.code).localeCompare(b.name || b.code, "es-CL")
        : b.updated_at.localeCompare(a.updated_at),
    );

  return (
    <div className="projects-home">
      <header className="projects-home__head">
        <div>
          <h1 className="projects-home__title" id="page-title">
            Obras
          </h1>
          <p className="projects-home__context">Lo que tiene {orgName} en curso.</p>
        </div>
        {canWrite ? (
          <Button
            variant="primary"
            className="projects-home__new"
            icon={<Icon name="plus" />}
            loading={creating}
            onClick={() => void startQuotation()}
          >
            Nueva cotización
          </Button>
        ) : null}
      </header>
      {createError ? <p role="alert">{createError}</p> : null}

      {noSystems ? (
        <section className="projects-home__prompt" aria-labelledby="catalog-prompt">
          <Icon name="catalogs" size={24} />
          <div>
            <h2 id="catalog-prompt">Para calcular precios necesitas un sistema</h2>
            <p>Sube el PDF del catálogo de tu proveedor. Mientras tanto puedes dibujar ventanas.</p>
          </div>
          <Link className="ui-button" to="/catalogs/systems?import=1">
            Importar catálogo
          </Link>
        </section>
      ) : null}

      {decisions.length > 0 ? (
        <section className="home-card" aria-labelledby="decide-title">
          <div className="home-card__head">
            <h2 id="decide-title">Necesita tu atención</h2>
            <Link className="ui-link" to="/dashboard">
              Ver todos los pendientes ({today.data?.actions.length ?? 0})
            </Link>
          </div>
          <ul className="decide-list">
            {decisions.slice(0, 4).map((group) => (
              <li key={group.name} className="decide-item">
                <span
                  className={`decide-item__dot${group.urgent ? " is-urgent" : ""}`}
                  aria-hidden="true"
                />
                <div className="decide-item__work">
                  <strong>{group.name}</strong>
                  <span>
                    {group.actions.length === 1
                      ? group.actions[0]!.title
                      : `${group.actions.length} decisiones · ${group.actions[0]!.title}`}
                    {group.urgent ? ` · ${group.urgent}` : ""}
                  </span>
                </div>
                <Link className="decide-item__action" to={group.actions[0]!.href}>
                  {capitalize(group.actions[0]!.verb)}
                </Link>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      <section className="projects-home__works" aria-labelledby="works-title">
        <div className="home-works__head">
          <h2 id="works-title">Obras</h2>
          <div className="projects-home__tools">
            <div className="home-segmented" role="radiogroup" aria-label="Estado">
              {FILTERS.map((filter) => (
                <button
                  key={filter.value || "all"}
                  type="button"
                  role="radio"
                  aria-checked={statusFilter === filter.value}
                  onClick={() => setParam("status", filter.value)}
                >
                  {filter.label}
                </button>
              ))}
            </div>
            <label className="home-search">
              <Icon name="search" size={16} />
              <span className="sr-only">Buscar obra o cliente</span>
              <input
                type="search"
                placeholder="Buscar obra o cliente"
                value={search}
                onChange={(event) => setParam("q", event.target.value)}
              />
            </label>
            <label className="home-sort">
              <span className="sr-only">Ordenar</span>
              <select
                value={sortKey}
                onChange={(event) => setParam("sort", event.target.value, "updated")}
              >
                <option value="updated">Más recientes</option>
                <option value="name">Por nombre</option>
              </select>
            </label>
          </div>
        </div>

        {items.length === 0 ? (
          <EmptyState
            title="Aún no hay cotizaciones"
            body="Empieza por la primera ventana; el cliente se completa cuando lo necesites."
            action={
              canWrite ? (
                <Button variant="primary" loading={creating} onClick={() => void startQuotation()}>
                  Nueva cotización
                </Button>
              ) : undefined
            }
          />
        ) : visible.length === 0 ? (
          <EmptyState
            title="Ninguna obra coincide"
            body="Cambia la búsqueda o el estado para ver más obras."
            action={
              <Button
                onClick={() =>
                  setParams((current) => {
                    const next = new URLSearchParams(current);
                    next.delete("q");
                    next.delete("status");
                    return next;
                  })
                }
              >
                Limpiar filtros
              </Button>
            }
          />
        ) : (
          <ul className="work-list">
            {visible.map((item) => (
              <li key={item.id} className="work-row">
                <span className="work-row__main">
                  <Link className="work-row__name" to={`/projects/${encodeURIComponent(item.id)}`}>
                    {item.name || item.code}
                  </Link>
                  <span className="work-row__meta">
                    {item.client_name || "Sin cliente todavía"} ·{" "}
                    <time dateTime={item.updated_at} title={formatDateTime(item.updated_at)}>
                      {formatRelativeTimestamp(item.updated_at)}
                    </time>
                  </span>
                </span>
                <span className="work-row__status">
                  <StatusBadge showIcon={false} data-status={item.status.toLowerCase()}>
                    {t(PROJECT_STATUS[item.status])}
                  </StatusBadge>
                </span>
                <span className="work-row__windows">
                  {item.position_count === 0
                    ? "Sin ventanas"
                    : item.position_count === 1
                      ? "1 ventana"
                      : `${item.position_count} ventanas`}
                </span>
                <span className={`work-row__total${item.pricing_current ? "" : " is-pending"}`}>
                  {item.pricing_current
                    ? formatMoney(item.total_price_gross, item.currency)
                    : item.position_count > 0
                      ? "Falta precio"
                      : ""}
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}

type DecisionGroup = { name: string; actions: TodayAction[]; urgent: string | null };

/** Decisions grouped by work, most consequential first (overdue, blocking). */
function groupDecisions(actions: readonly TodayAction[]): DecisionGroup[] {
  const rank: Record<string, number> = { overdue: 0, blocking: 1, today: 2, follow_up: 3 };
  const groups = new Map<string, TodayAction[]>();
  for (const action of actions) {
    const name = action.entity_name || action.entity_code;
    groups.set(name, [...(groups.get(name) ?? []), action]);
  }
  return [...groups.entries()]
    .map(([name, list]) => {
      const sorted = [...list].sort(
        (a, b) => (rank[a.consequence] ?? 9) - (rank[b.consequence] ?? 9),
      );
      const top = sorted[0]!.consequence;
      return {
        name,
        actions: sorted,
        urgent: top === "overdue" ? "Vencido" : top === "blocking" ? "Bloquea a otros" : null,
      };
    })
    .sort(
      (a, b) => (rank[a.actions[0]!.consequence] ?? 9) - (rank[b.actions[0]!.consequence] ?? 9),
    );
}

function capitalize(value: string): string {
  return value ? value.charAt(0).toLocaleUpperCase("es-CL") + value.slice(1) : value;
}
