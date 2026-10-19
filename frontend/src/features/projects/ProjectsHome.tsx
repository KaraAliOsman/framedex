import { useMemo, useRef, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

import { ApiError } from "../../api/apiMutator";
import { engineSystems, projectsCreate } from "../../api/generated/dekopen";
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

/** A new quotation is named by its day until the person names it. */
export function draftQuotationName(now = new Date()): string {
  const day = now.toLocaleDateString("es-CL", {
    day: "numeric",
    month: "long",
    timeZone: "America/Santiago",
  });
  return `Cotización del ${day}`;
}

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
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [params, setParams] = useSearchParams();
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState("");
  const lock = useRef(false);

  const search = params.get("q") ?? "";
  const statusFilter = params.get("status") ?? "";
  // Large practices open on the table; the choice is remembered in the URL.
  const view = params.get("view") ?? (items.length > 24 ? "table" : "gallery");
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

  async function startQuotation(): Promise<void> {
    if (lock.current) return;
    lock.current = true;
    setCreating(true);
    setCreateError("");
    try {
      const response = await projectsCreate(
        { name: draftQuotationName(), client_name: "" },
        { headers: { "X-Organization-ID": orgId } },
      );
      if (response.status !== 201) throw new ApiError(response.status, response.data);
      void queryClient.invalidateQueries({ queryKey: ["project-pages"] });
      navigate(`/projects/${encodeURIComponent(response.data.id)}/positions/new`);
    } catch (caught) {
      const status = caught instanceof ApiError ? caught.status : null;
      setCreateError(
        status === 403
          ? "Tu rol no puede crear cotizaciones. Pide acceso de estimador al dueño."
          : "No se pudo crear la cotización. Revisa la conexión y vuelve a intentarlo.",
      );
    } finally {
      lock.current = false;
      setCreating(false);
    }
  }

  return (
    <div className="projects-home">
      <header className="projects-home__head">
        <div>
          <h1 className="projects-home__title" id="page-title">
            Proyectos
          </h1>
          <p className="projects-home__context">{orgName}</p>
        </div>
        <div className="projects-home__actions">
          <label className="projects-home__search">
            <Icon name="search" size={16} />
            <span className="sr-only">Buscar obra o cliente</span>
            <input
              type="search"
              placeholder="Buscar obra o cliente"
              value={search}
              onChange={(event) => setParam("q", event.target.value)}
            />
          </label>
          {canWrite ? (
            <Button
              variant="primary"
              icon={<Icon name="plus" />}
              loading={creating}
              onClick={() => void startQuotation()}
            >
              Nueva cotización
            </Button>
          ) : null}
        </div>
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
        <section className="projects-home__decide" aria-labelledby="decide-title">
          <div className="projects-home__section-head">
            <h2 id="decide-title">Necesita tu atención</h2>
            <Link className="ui-link" to="/dashboard">
              Ver todos los pendientes ({today.data?.actions.length ?? 0})
            </Link>
          </div>
          <ul className="decide-list">
            {decisions.slice(0, 4).map((group) => (
              <li key={group.name} className="decide-item">
                <div className="decide-item__work">
                  <strong>{group.name}</strong>
                  <span>
                    {group.actions.length === 1
                      ? group.actions[0]!.title
                      : `${group.actions.length} decisiones · ${group.actions[0]!.title}`}
                  </span>
                </div>
                {group.urgent ? (
                  <StatusBadge tone="warning" showIcon={false}>
                    {group.urgent}
                  </StatusBadge>
                ) : null}
                <Link className="ui-button ui-button--compact" to={group.actions[0]!.href}>
                  {capitalize(group.actions[0]!.verb)}
                </Link>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      <section className="projects-home__works" aria-labelledby="works-title">
        <div className="projects-home__section-head">
          <h2 id="works-title">Trabajos</h2>
          <div className="projects-home__tools">
            <div
              className="ui-segmented projects-home__filters"
              role="radiogroup"
              aria-label="Estado"
            >
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
            <label className="projects-home__sort">
              <span className="sr-only">Ordenar</span>
              <select
                value={sortKey}
                onChange={(event) => setParam("sort", event.target.value, "updated")}
              >
                <option value="updated">Más recientes</option>
                <option value="name">Por nombre</option>
              </select>
            </label>
            <div className="ui-segmented" role="radiogroup" aria-label="Vista">
              <button
                type="button"
                role="radio"
                aria-checked={view === "gallery"}
                aria-label="Galería"
                title="Galería"
                onClick={() => setParam("view", "gallery")}
              >
                <Icon name="grid" size={16} />
              </button>
              <button
                type="button"
                role="radio"
                aria-checked={view === "table"}
                aria-label="Tabla"
                title="Tabla"
                onClick={() => setParam("view", "table")}
              >
                <Icon name="list" size={16} />
              </button>
            </div>
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
            title="Ningún trabajo coincide"
            body="Cambia la búsqueda o el estado para ver más trabajos."
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
        ) : view === "gallery" ? (
          <ul className="work-grid">
            {visible.map((item) => (
              <li key={item.id}>
                <Link className="work-card" to={`/projects/${encodeURIComponent(item.id)}`}>
                  <span className="work-card__top">
                    <StatusBadge showIcon={false} data-status={item.status.toLowerCase()}>
                      {t(PROJECT_STATUS[item.status])}
                    </StatusBadge>
                    <time dateTime={item.updated_at} title={formatDateTime(item.updated_at)}>
                      {formatRelativeTimestamp(item.updated_at)}
                    </time>
                  </span>
                  <span className="work-card__name">{item.name || item.code}</span>
                  <span className={`work-card__client${item.client_name ? "" : " is-missing"}`}>
                    {item.client_name || "Sin cliente todavía"}
                  </span>
                  <span className="work-card__foot">
                    <span>
                      {item.position_count === 0
                        ? "Sin ventanas todavía"
                        : item.position_count === 1
                          ? "1 ventana"
                          : `${item.position_count} ventanas`}
                    </span>
                    {item.pricing_current ? (
                      <span className="work-card__total">
                        {formatMoney(item.total_price_gross, item.currency)}
                      </span>
                    ) : item.position_count > 0 ? (
                      <span className="work-card__total is-pending">Falta precio</span>
                    ) : null}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        ) : (
          <div className="work-table-wrap">
            <table className="ui-data-table work-table">
              <thead>
                <tr>
                  <th scope="col">Obra</th>
                  <th scope="col">Cliente</th>
                  <th scope="col">Estado</th>
                  <th scope="col" className="is-numeric">
                    Ventanas
                  </th>
                  <th scope="col" className="is-numeric">
                    Total
                  </th>
                  <th scope="col">Actualizado</th>
                </tr>
              </thead>
              <tbody>
                {visible.map((item) => (
                  <tr key={item.id}>
                    <td>
                      <Link to={`/projects/${encodeURIComponent(item.id)}`}>
                        {item.name || item.code}
                      </Link>
                      <span className="work-table__code">{item.code}</span>
                    </td>
                    <td className={item.client_name ? undefined : "is-missing"}>
                      {item.client_name || "Sin cliente"}
                    </td>
                    <td>
                      <StatusBadge showIcon={false} data-status={item.status.toLowerCase()}>
                        {t(PROJECT_STATUS[item.status])}
                      </StatusBadge>
                    </td>
                    <td className="is-numeric">{item.position_count}</td>
                    <td className="is-numeric">
                      {item.pricing_current
                        ? formatMoney(item.total_price_gross, item.currency)
                        : "Sin precio"}
                    </td>
                    <td>
                      <time dateTime={item.updated_at} title={formatDateTime(item.updated_at)}>
                        {formatRelativeTimestamp(item.updated_at)}
                      </time>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
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
