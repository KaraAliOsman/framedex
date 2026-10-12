import { useQuery } from "@tanstack/react-query";
import { Link, useSearchParams } from "react-router-dom";
import { analyticsQuotations } from "../../api/generated/dekopen";
import { ApiError } from "../../api/apiMutator";
import type { AnalyticsQuotationsParams } from "../../api/generated/models";
import { useAuthSession } from "../../auth/AuthSessionProvider";
import { formatRevision } from "../../format";
import {
  DateOnly,
  DeniedState,
  ErrorState,
  LoadingState,
  Money,
  PageHeader,
  Timestamp,
} from "../../ui";
import { phaseLabels } from "../../app/todayLabels";
import "./quotations.css";

export const quoteStates: Record<string, string> = {
  pending: "Espera respuesta",
  approved: "Aprobada",
  response: "Respuesta por revisar",
  unshared: "Sin enlace vigente",
  expired: "Vigencia terminada",
  link_expired: "Enlace vencido",
};
const filters: Record<string, string> = {
  "": "Todas",
  expiring: "Vencen en tres días",
  viewed: "Vistas sin respuesta",
  response: "Respuesta del cliente",
  expired: "Vencidas",
  unshared: "Sin enlace vigente",
  pending: "Espera respuesta",
  approved: "Aprobadas",
  link_expired: "Enlace vencido",
};

export function QuotationsPage(): JSX.Element {
  const org = useAuthSession().me?.active_organization;
  if (!org || !["OWNER", "ESTIMATOR"].includes(org.role))
    return (
      <DeniedState reason="El dueño y el estimador consultan cotizaciones. Solicita acceso al dueño." />
    );
  return <QuotationIndex key={org.id} orgId={org.id} />;
}

function QuotationIndex({ orgId }: { orgId: string }): JSX.Element {
  const [params, setParams] = useSearchParams();
  const needle = params.get("q") ?? "";
  const attention = params.get("attention") ?? "";
  const phase = params.get("phase") ?? "";
  const currency = params.get("currency") ?? "";
  const offset = Math.max(0, Number(params.get("offset") ?? 0) || 0);
  function filter(key: string, value: string): void {
    const next = new URLSearchParams(params);
    if (value) next.set(key, value);
    else next.delete(key);
    if (key !== "offset") next.delete("offset");
    setParams(next, { replace: key === "q" });
  }
  const query = useQuery({
    queryKey: ["quotations", orgId, needle, attention, phase, currency, offset],
    queryFn: async ({ signal }) => {
      const response = await analyticsQuotations(
        { q: needle, attention, phase, currency, offset, limit: 50 } as AnalyticsQuotationsParams,
        { signal, headers: { "X-Organization-ID": orgId } },
      );
      if (response.status !== 200) throw new ApiError(response.status, response.data);
      return response.data;
    },
  });
  return (
    <section className="quotations-page" data-density="office">
      <PageHeader title="Cotizaciones" context="Revisiones emitidas vigentes por proyecto" />
      <div className="quote-filters">
        <label>
          Buscar proyecto o cliente
          <input
            className="ui-field__input"
            type="search"
            maxLength={80}
            value={needle}
            onChange={(e) => filter("q", e.target.value)}
          />
        </label>
        <label>
          Seguimiento
          <select
            className="ui-field__input"
            value={attention}
            onChange={(e) => filter("attention", e.target.value)}
          >
            {Object.entries(filters).map(([key, label]) => (
              <option value={key} key={key}>
                {label}
              </option>
            ))}
          </select>
        </label>
        <label>
          Fase
          <select
            className="ui-field__input"
            value={phase}
            onChange={(e) => filter("phase", e.target.value)}
          >
            <option value="">Todas</option>
            {Object.entries(phaseLabels).map(([key, label]) => (
              <option value={key} key={key}>
                {label}
              </option>
            ))}
          </select>
        </label>
        <label>
          Moneda
          <select
            className="ui-field__input"
            value={currency}
            onChange={(e) => filter("currency", e.target.value)}
          >
            <option value="">Todas</option>
            <option value="CLP">Peso chileno</option>
            <option value="USD">Dólar</option>
            <option value="UF">Unidad de fomento</option>
            <option value="unknown">Sin moneda sellada</option>
          </select>
        </label>
      </div>
      {query.isPending ? (
        <LoadingState label="Cargando cotizaciones" />
      ) : query.isError ? (
        <ErrorState
          title="No se pudieron cargar las cotizaciones"
          body="La revisión emitida se conserva. Reintenta la consulta."
          onRetry={() => void query.refetch()}
        />
      ) : query.data.items.length === 0 ? (
        <div className="quote-empty">
          <h2>No hay cotizaciones en esta lista</h2>
          <p>
            {needle || attention || phase || currency
              ? "Cambia los filtros para ver otras revisiones."
              : "Las cotizaciones aparecen aquí al emitir una revisión de un proyecto."}
          </p>
          {needle || attention || phase || currency ? (
            <button type="button" onClick={() => setParams({})}>
              Ver todas
            </button>
          ) : (
            <Link className="ui-button" to="/projects">
              Abrir proyectos
            </Link>
          )}
        </div>
      ) : (
        <>
          <table className="quote-index">
            <thead>
              <tr>
                <th>Proyecto y revisión</th>
                <th>Seguimiento</th>
                <th>Vigencia</th>
                <th>Cliente</th>
                <th>Total con IVA</th>
              </tr>
            </thead>
            <tbody>
              {query.data.items.map((item) => (
                <tr key={item.project_id}>
                  <td>
                    <Link to={item.href} className="quote-project">
                      <span className="ui-value">
                        {item.project_code} · {formatRevision(item.revision_code)}
                      </span>
                      <strong>{item.project_name}</strong>
                    </Link>
                  </td>
                  <td>
                    <span className="quote-state">
                      {quoteStates[item.state] ?? "Sin dato · estado sin reconocer"}
                    </span>
                    <p>{phaseLabels[item.phase] ?? "Sin dato · falta fase"}</p>
                    <p>
                      {item.view_count > 0 ? (
                        <>
                          <span className="ui-value">{item.view_count}</span>{" "}
                          {item.view_count === 1 ? "vista" : "vistas"} ·{" "}
                          <Timestamp value={item.last_viewed_at} />
                        </>
                      ) : (
                        "Sin vistas registradas"
                      )}
                    </p>
                    {item.response_note && (
                      <details>
                        <summary>Respuesta del cliente</summary>
                        <p>{item.response_note}</p>
                      </details>
                    )}
                  </td>
                  <td>
                    {item.valid_until ? (
                      <DateOnly value={item.valid_until} />
                    ) : (
                      "Sin dato · falta vigencia sellada"
                    )}
                  </td>
                  <td>{item.client_name || "Sin cliente registrado"}</td>
                  <td>
                    {item.currency ? (
                      <Money
                        value={item.total}
                        currency={item.currency}
                        cause="Falta el total sellado de esta revisión"
                      />
                    ) : (
                      "Sin dato · falta moneda sellada"
                    )}
                    <details className="quote-source">
                      <summary>¿De dónde sale?</summary>
                      <p>{item.source}</p>
                    </details>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <nav className="quote-pagination" aria-label="Páginas de cotizaciones">
            <button
              type="button"
              disabled={offset === 0}
              onClick={() => filter("offset", String(Math.max(0, offset - 50)))}
            >
              Anterior
            </button>
            <span className="ui-value">
              {offset + 1}–{Math.min(offset + query.data.items.length, query.data.total)} de{" "}
              {query.data.total}
            </span>
            <button
              type="button"
              disabled={offset + 50 >= query.data.total}
              onClick={() => filter("offset", String(offset + 50))}
            >
              Siguiente
            </button>
          </nav>
        </>
      )}
    </section>
  );
}
