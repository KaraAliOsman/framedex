import { useInfiniteQuery, type InfiniteData } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { ApiError } from "../../api/apiMutator";
import { aiUsageList } from "../../api/generated/dekopen";
import { useAuthSession } from "../../auth/AuthSessionProvider";
import { formatDateTime, formatDecimal } from "../../format";
import {
  Button,
  DeniedState,
  DimLoader,
  EmptyState,
  ErrorState,
  Skeleton,
  UnknownValue,
} from "../../ui";
import type { AiUsageWork } from "../../api/generated/models";
import { AiCost } from "./AiCost";
import { AI_CAPABILITIES, AI_TOOLS } from "./providerLabels";
import "./providerOperations.css";

const STATES: Record<string, string> = {
  RUNNING: "En curso",
  QUEUED: "En cola",
  SUCCEEDED: "Completado",
  FAILED: "Falló",
  CANCELED: "Cancelado",
};

export function AiWorkList({
  capability,
  state,
}: {
  capability: string;
  state: string;
}): JSX.Element {
  const me = useAuthSession().me;
  const org = me?.active_organization;
  const query = useInfiniteQuery<
    AiUsageWork[],
    Error,
    InfiniteData<AiUsageWork[]>,
    readonly unknown[],
    number
  >({
    queryKey: ["ai", "work", org?.id, capability, state],
    enabled: !!org,
    initialPageParam: 0,
    getNextPageParam: (last, _pages, offset) => (last.length === 100 ? offset + 100 : undefined),
    refetchInterval: (result) =>
      result.state.data?.pages.some((page) => page.some((work) => work.status === "RUNNING"))
        ? 2500
        : 30000,
    queryFn: async ({ signal, pageParam }): Promise<AiUsageWork[]> => {
      const response = await aiUsageList(
        {
          capability: capability === "all_ai" ? undefined : capability,
          state: state || undefined,
          limit: 100,
          offset: pageParam,
        },
        { signal, headers: { "X-Organization-ID": org!.id } },
      );
      if (response.status !== 200) throw new ApiError(response.status, response.data);
      return response.data;
    },
  });
  if (query.isPending)
    return (
      <>
        <Skeleton lines={4} />
        <DimLoader label="Consultando las llamadas del proveedor" />
      </>
    );
  if (query.error instanceof ApiError && query.error.status === 403)
    return (
      <DeniedState reason="El dueño, el estimador y el encargado de taller pueden revisar estas llamadas. Pide acceso al dueño." />
    );
  if (query.isError)
    return (
      <ErrorState
        title="No se pudo consultar el uso de IA"
        body="Revisa la conexión y reintenta para ver el costo y las herramientas usadas."
        onRetry={() => void query.refetch()}
      />
    );
  const workItems = query.data?.pages.flat() ?? [];
  if (workItems.length === 0)
    return (
      <EmptyState
        title="No hay llamadas de IA con estos filtros"
        body="El registro aparece cuando un trabajo consulta al proveedor."
        action={
          <Link className="ui-button" to="/assistant">
            Abrir asistente
          </Link>
        }
      />
    );
  return (
    <div className="ai-work-list" data-density="office">
      <p className="settings-hint">
        {org?.role === "OWNER"
          ? "Llamadas de tu organización."
          : "Tus llamadas dentro de esta organización."}{" "}
        El costo usa los tokens informados y la tarifa declarada al iniciar cada llamada.
      </p>
      {workItems.map((work) => (
        <article key={work.id} className="ai-work">
          <header>
            <strong>{AI_CAPABILITIES[work.capability] ?? "Consultar al proveedor"}</strong>
            <span
              className="status-chip"
              data-status={(work.job_state ?? work.status).toLowerCase()}
            >
              {STATES[work.job_state ?? work.status] ?? "Sin dato"}
            </span>
            {work.test_mode && <span className="status-chip">Modo de prueba</span>}
            <time dateTime={work.created_at}>{formatDateTime(work.created_at)}</time>
            {work.ai_job_id && work.user_id === me?.user.id && (
              <Link
                className="ui-button ui-button--small ui-button--ghost"
                to={`/assistant?job=${work.ai_job_id}`}
              >
                Ver propuesta
              </Link>
            )}
          </header>
          <dl>
            <div>
              <dt>Persona</dt>
              <dd>
                {work.user_label ?? (
                  <UnknownValue cause="El usuario ya no tiene un nombre disponible" />
                )}
              </dd>
            </div>
            <div>
              <dt>Llamadas</dt>
              <dd className="ai-number">{formatDecimal(work.calls, 0)}</dd>
            </div>
            <div>
              <dt>Tokens de entrada / salida</dt>
              <dd className="ai-number">
                {work.tokens_prompt === null || work.tokens_completion === null ? (
                  <UnknownValue cause="El proveedor no informó todos los tokens" />
                ) : (
                  `${formatDecimal(work.tokens_prompt, 0)} / ${formatDecimal(work.tokens_completion, 0)}`
                )}
              </dd>
            </div>
            <div>
              <dt>Costo estimado</dt>
              <dd>
                <AiCost value={work.estimated_cost_usd} />
              </dd>
            </div>
            <div>
              <dt>Tiempo del proveedor</dt>
              <dd className="ai-number">
                {work.latency_ms === null ? (
                  <UnknownValue cause="La llamada aún no termina o falló sin medición" />
                ) : (
                  `${formatDecimal(String(work.latency_ms / 1000), 3)} s`
                )}
              </dd>
            </div>
          </dl>
          {work.last_cause && <p className="ai-requires-person">{work.last_cause}</p>}
          <details className="ai-advanced">
            <summary>¿De dónde sale? · Traza del trabajo</summary>
            <p>
              Registro del proveedor: {STATES[work.status] ?? "Sin dato"}.{" "}
              {work.fallback
                ? "El modelo respondió mediante JSON validado después de rechazar herramientas nativas."
                : "La respuesta conserva la validación del servidor."}
            </p>
            <p>
              <span className="ai-number">{formatDecimal(work.retries, 0)}</span> reintentos
              transitorios ·{" "}
              <span className="ai-number">{formatDecimal(work.capacity_credits, 0)} créditos</span>{" "}
              de solicitudes.
            </p>
            {work.trace.length ? (
              <ul>
                {work.trace.map((entry, index) => (
                  <li key={index}>
                    {AI_TOOLS[entry.tool!] ?? "Consultar contexto autorizado"} ·{" "}
                    {entry.status === "ERROR"
                      ? "Bloqueado"
                      : entry.status === "CACHED"
                        ? "Resultado reutilizado"
                        : "Consultado"}
                  </li>
                ))}
              </ul>
            ) : (
              <p>
                No hay herramientas ejecutadas registradas para esta llamada. La propuesta y sus
                consultas están en el asistente.
              </p>
            )}
            {work.estimated_cost_usd === null && (
              <p>
                Sin tarifa monetaria para estas llamadas. El dueño puede declararla en{" "}
                <Link to="/settings/general#inteligencia-artificial">
                  Ajustes › Inteligencia artificial
                </Link>
                . Las llamadas anteriores mantienen su fuente original.
              </p>
            )}
          </details>
        </article>
      ))}
      {query.hasNextPage && (
        <Button disabled={query.isFetchingNextPage} onClick={() => void query.fetchNextPage()}>
          Cargar más llamadas
        </Button>
      )}
    </div>
  );
}
