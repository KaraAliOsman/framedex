import { useQuery } from "@tanstack/react-query";
import { Link, useSearchParams } from "react-router-dom";
import { ApiError } from "../../api/apiMutator";
import { engineSystems } from "../../api/generated/dekopen";
import type { ProjectResponse } from "../../api/generated/models";
import { formatRelativeTimestamp } from "../../decimal";
import { formatDateTime } from "../../format";
import { Button, EmptyState, Icon, Money, StatusBadge } from "../../ui";
import { useNewQuotation } from "./useNewQuotation";
import {
  filterWorks,
  pageOffset,
  workAmount,
  workStages,
  workStageTone,
  legacyStatuses,
} from "./worksList";
import "./projects-home.css";
export { draftQuotationName } from "./useNewQuotation";

/** One list of works, using the backend's real stage and current revision. */
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
  const stage = params.get("stage") ?? "";
  const legacyStatus = params.get("status") ?? "";
  const sort = params.get("sort") ?? "updated";
  const matching = filterWorks(items, search, legacyStatus, sort);
  const filtered = matching.filter((item) => !stage || item.progress?.stage === stage);
  const offset = Math.min(
    pageOffset(params.get("offset")),
    Math.max(0, Math.ceil(filtered.length / 50) - 1) * 50,
  );
  const visible = filtered.slice(offset, offset + 50);
  function setParam(key: string, value: string, fallback = ""): void {
    setParams(
      (current) => {
        const next = new URLSearchParams(current);
        if (value && value !== fallback) next.set(key, value);
        else next.delete(key);
        if (key !== "offset") next.delete("offset");
        if (key === "stage") next.delete("status");
        return next;
      },
      { replace: key === "q" },
    );
  }
  function clearFilters() {
    setParams((current) => {
      const next = new URLSearchParams(current);
      for (const key of ["q", "stage", "status", "offset"]) next.delete(key);
      return next;
    });
  }
  const systems = useQuery({
    queryKey: ["project-systems", orgId],
    queryFn: async ({ signal }) => {
      const response = await engineSystems({ signal, headers: { "X-Organization-ID": orgId } });
      if (response.status !== 200) throw new ApiError(response.status, response.data);
      return response.data.systems;
    },
    retry: false,
    staleTime: 60_000,
  });
  return (
    <section className="projects-home" aria-labelledby="page-title">
      <header className="projects-home__head">
        <div>
          <h1 className="projects-home__title" id="page-title">
            Obras
          </h1>
          <p className="projects-home__context">{orgName}</p>
        </div>
        {canWrite && (
          <Button
            variant="primary"
            icon={<Icon name="plus" />}
            loading={creating}
            onClick={() => void startQuotation()}
          >
            Nueva cotización
          </Button>
        )}
      </header>
      {createError && <p role="alert">{createError}</p>}
      {canWrite && systems.isSuccess && systems.data.length === 0 && (
        <section className="projects-home__prompt" aria-labelledby="catalog-prompt">
          <Icon name="catalogs" size={24} />
          <div>
            <h2 id="catalog-prompt">Para calcular precios necesitas una serie</h2>
            <p>Sube el PDF de tu proveedor. Mientras tanto puedes dibujar ventanas.</p>
          </div>
          <Link className="ui-button" to="/catalogs/systems?import=1">
            Importar catálogo
          </Link>
        </section>
      )}
      <div className="projects-home__tools">
        <div className="home-segmented ui-segmented" role="group" aria-label="Etapa">
          <button
            type="button"
            aria-pressed={!stage && !legacyStatus}
            onClick={() => setParam("stage", "")}
          >
            Todas · {matching.length}
          </button>
          {Object.entries(workStages).map(([value, label]) => (
            <button
              key={value}
              type="button"
              aria-pressed={stage === value}
              onClick={() => setParam("stage", value)}
            >
              {label} · {matching.filter((item) => item.progress?.stage === value).length}
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
            maxLength={255}
            onChange={(event) => setParam("q", event.target.value)}
          />
        </label>
        <label className="home-sort">
          <span className="sr-only">Ordenar</span>
          <select
            value={sort}
            onChange={(event) => setParam("sort", event.target.value, "updated")}
          >
            <option value="updated">Más recientes</option>
            <option value="name">Por nombre</option>
          </select>
        </label>
      </div>
      {legacyStatus && (
        <p className="works-legacy-filter">
          Filtro de estado guardado: {legacyStatuses[legacyStatus] ?? "Revisar estado"}.{" "}
          <button type="button" onClick={() => setParam("status", "")}>
            Quitar filtro
          </button>
        </p>
      )}
      {items.length === 500 && (
        <p className="works-limit">La consulta incluye hasta las 500 obras más recientes.</p>
      )}
      {items.length === 0 ? (
        <EmptyState
          title="Aún no hay cotizaciones"
          body="Empieza por la primera ventana; el cliente se completa cuando lo necesites."
        />
      ) : filtered.length === 0 ? (
        <EmptyState
          title="Ninguna obra coincide"
          body="Cambia la búsqueda o la etapa para ver más obras."
          action={<Button onClick={clearFilters}>Limpiar filtros</Button>}
        />
      ) : (
        <div className="works-table">
          <div className="work-columns" aria-hidden="true">
            <span>Obra</span>
            <span>Etapa</span>
            <span>Ventanas</span>
            <span>Total con IVA</span>
            <span>Última actividad</span>
          </div>
          <ul className="work-list" aria-label="Obras">
            {visible.map((item) => {
              const amount = workAmount(item);
              return (
                <li key={item.id}>
                  <Link className="work-row" to={`/projects/${encodeURIComponent(item.id)}`}>
                    <span className="work-row__main">
                      <strong className="work-row__name">{item.name || item.code}</strong>
                      <span className="work-row__meta">
                        {item.client_name || "Agrega el cliente"}
                      </span>
                      <span className="work-row__code ui-value">{item.code}</span>
                    </span>
                    <span className="work-row__status" title={item.progress?.reason}>
                      <StatusBadge
                        showIcon={false}
                        tone={item.progress ? workStageTone[item.progress.stage] : "unknown"}
                      >
                        {item.progress ? workStages[item.progress.stage] : "Revisar etapa"}
                      </StatusBadge>
                    </span>
                    <span className="work-row__windows">
                      <span className="work-row__windows-label">Ventanas: </span>
                      {item.position_count}
                    </span>
                    <span className="work-row__total" title={amount?.origin}>
                      {amount ? (
                        <Money value={amount.value} currency={amount.currency} />
                      ) : item.position_count > 0 ? (
                        "Abre para calcular"
                      ) : (
                        "Añade ventanas"
                      )}
                    </span>
                    <time
                      className="work-row__activity"
                      dateTime={item.updated_at}
                      title={formatDateTime(item.updated_at)}
                    >
                      {formatRelativeTimestamp(item.updated_at)}
                    </time>
                  </Link>
                </li>
              );
            })}
          </ul>
        </div>
      )}
      {filtered.length > 50 && (
        <nav className="works-pagination" aria-label="Páginas de obras">
          <Button disabled={offset === 0} onClick={() => setParam("offset", String(offset - 50))}>
            Anterior
          </Button>
          <span className="ui-value">
            {offset + 1}–{Math.min(offset + 50, filtered.length)} de {filtered.length} obras
          </span>
          <Button
            disabled={offset + 50 >= filtered.length}
            onClick={() => setParam("offset", String(offset + 50))}
          >
            Siguiente
          </Button>
        </nav>
      )}
    </section>
  );
}
