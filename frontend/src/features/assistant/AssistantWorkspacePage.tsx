import { useCallback, useMemo, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useLocation, useSearchParams } from "react-router-dom";
import { aiJobList, aiJobRetrieve, projectsList } from "../../api/generated/dekopen";
import type { AiJob, AiJobDetail } from "../../api/generated/models";
import { ApiError } from "../../api/apiMutator";
import { useAuthSession } from "../../auth/AuthSessionProvider";
import { DeniedState, ErrorState, LoadingState } from "../../ui";
import { Icon, type IconName } from "../../ui/Icon";
import { formatDateTime } from "../../format";
import { AgentBody } from "./AgentBody";
import { Orb, orbStateFor } from "./Orb";
import { STATE_LABELS } from "./states";
import { useAssistantSurface } from "./assistantContext";
import { AiMetricsCard } from "./AiMetricsCard";
import { t } from "../../i18n/es-CL";
import "./assistant.css";
import "./assistant-room.css";

const LIVE = new Set(["QUEUED", "PLANNING", "RUNNING"]);
const IDEAS: { icon: IconName; title: string; text: string; goal?: string; href?: string }[] = [
  {
    icon: "window",
    title: "Diseñar una ventana",
    text: "De tus medidas al diseño",
    goal: "Quiero diseñar una ventana. Usa las preferencias de mi empresa y ayúdame solo con los datos imprescindibles.",
  },
  {
    icon: "document",
    title: "Preparar una cotización",
    text: "Ventanas, precio y PDF",
    goal: "Prepara toda la cotización de esta obra con las preferencias guardadas de mi empresa. Muéstrame una muestra para revisar.",
  },
  {
    icon: "edit",
    title: "Mejorar mi PDF",
    text: "Presentación y textos",
    goal: "Mejora la presentación del PDF de cotización: una propuesta clara, con dibujos protagonistas y textos breves. Prepara una muestra antes de aplicar.",
  },
  {
    icon: "catalog",
    title: "Importar un catálogo",
    text: "Empieza con el PDF",
    href: "/catalogs/systems?import=new",
  },
];

export function AssistantWorkspacePage(): JSX.Element {
  const auth = useAuthSession();
  const org = auth.me?.active_organization;
  if (!org || !["OWNER", "ESTIMATOR", "WORKSHOP_MANAGER"].includes(org.role))
    return <DeniedState reason="Tu rol no tiene acceso al asistente." />;
  return (
    <AssistantRoom
      key={`${org.id}:${auth.me?.user.id}`}
      organizationId={org.id}
      userId={auth.me?.user.id}
      owner={org.role === "OWNER"}
    />
  );
}

function AssistantRoom({
  organizationId,
  userId,
  owner,
}: {
  organizationId: string;
  userId?: string;
  owner: boolean;
}): JSX.Element {
  const location = useLocation();
  const [params, setParams] = useSearchParams();
  const selected = params.get("job");
  const queryClient = useQueryClient();
  const headers = useMemo(
    () => ({ headers: { "X-Organization-ID": organizationId } }),
    [organizationId],
  );
  const [projectId, setProjectId] = useState(params.get("project") ?? "");
  const [epoch, setEpoch] = useState(0);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [older, setOlder] = useState<AiJob[]>([]);
  const [loadingMore, setLoadingMore] = useState(false);
  const [noMore, setNoMore] = useState(false);
  const [historyError, setHistoryError] = useState("");
  const [draft, setDraft] = useState<{ text: string; request: number } | null>(() => {
    const text = (location.state as { assistantDraft?: unknown } | null)?.assistantDraft;
    return typeof text === "string" && text ? { text, request: 1 } : null;
  });
  const [current, setCurrent] = useState<AiJobDetail | null>(null);
  const jobs = useQuery({
    queryKey: ["ai", "jobs", organizationId],
    queryFn: async () => {
      const result = await aiJobList(undefined, headers);
      if (result.status !== 200) throw new ApiError(result.status, result.data);
      return result.data as AiJob[];
    },
    refetchInterval: (query) =>
      query.state.data?.some((job) => LIVE.has(job.state)) ? 4000 : false,
  });
  const detail = useQuery({
    queryKey: ["ai", "jobs", organizationId, selected],
    enabled: Boolean(selected),
    queryFn: async () => {
      const result = await aiJobRetrieve(selected!, headers);
      if (result.status !== 200) throw new ApiError(result.status, result.data);
      return result.data;
    },
  });
  const projects = useQuery({
    queryKey: ["assistant", "projects", organizationId],
    queryFn: async () => {
      const result = await projectsList(headers);
      if (result.status !== 200) throw new ApiError(result.status, result.data);
      return result.data.items;
    },
  });
  const bound = selected ? detail.data : null;
  const surface = bound?.surface ?? (projectId ? "project" : "assistant");
  const refs = useMemo(
    () => (bound?.refs as Record<string, string>) ?? (projectId ? { project_id: projectId } : {}),
    [bound?.refs, projectId],
  );
  useAssistantSurface(surface, refs);
  const onJob = useCallback(
    (job: AiJobDetail) => {
      setCurrent(job);
      queryClient.setQueryData<AiJob[]>(["ai", "jobs", organizationId], (old) => [
        job,
        ...(old ?? []).filter((entry) => entry.id !== job.id),
      ]);
    },
    [queryClient, organizationId],
  );
  const allJobs = [
    ...new Map([...(jobs.data ?? []), ...older].map((job) => [job.id, job])).values(),
  ];
  const historyEmpty = allJobs.length === 0;
  const canLoadMore = allJobs.length >= 30 && !noMore;
  async function more(): Promise<void> {
    const last = allJobs.at(-1);
    if (!last || loadingMore) return;
    setLoadingMore(true);
    setHistoryError("");
    try {
      const result = await aiJobList({ before: last.created_at, before_id: last.id }, headers);
      if (result.status !== 200) throw new Error();
      const page = result.data as AiJob[];
      setOlder((old) => [...old, ...page]);
      setNoMore(page.length < 30);
    } catch {
      setHistoryError("No se pudieron cargar más conversaciones. Reintenta.");
    } finally {
      setLoadingMore(false);
    }
  }
  function fresh(): void {
    setParams({});
    setCurrent(null);
    setDraft(null);
    setEpoch((value) => value + 1);
    setHistoryOpen(false);
  }
  function choose(id: string): void {
    setParams({ job: id });
    setCurrent(null);
    setDraft(null);
    setHistoryOpen(false);
  }
  return (
    <section
      className={`assistant-room${historyOpen ? " assistant-room--history-open" : ""}`}
      aria-label="Asistente DEKOPEN"
    >
      <aside className="assistant-history" aria-label="Tus conversaciones">
        <div className="assistant-history__head">
          <span>Tu asistente</span>
          <button
            type="button"
            className="ui-icon-button"
            onClick={() => setHistoryOpen(false)}
            aria-label="Ocultar conversaciones"
          >
            <Icon name="close" size={18} />
          </button>
        </div>
        <button
          type="button"
          className="ui-button ui-button--primary assistant-history__new"
          onClick={fresh}
        >
          <Icon name="plus" size={18} />
          Nuevo encargo
        </button>
        <h2>Conversaciones</h2>
        {jobs.isPending ? (
          <p className="assistant-muted">Cargando historial…</p>
        ) : jobs.isError ? (
          <button type="button" onClick={() => void jobs.refetch()}>
            Reintentar historial
          </button>
        ) : historyEmpty ? (
          <p className="assistant-muted">
            Tu primer encargo empieza aquí. Podrás retomarlo cuando quieras.
          </p>
        ) : (
          <ul>
            {allJobs.map((job) => (
              <li key={job.id}>
                <button
                  type="button"
                  className="assistant-history__job"
                  aria-current={(current?.id ?? selected) === job.id ? "true" : undefined}
                  onClick={() => choose(job.id)}
                >
                  <Orb state={orbStateFor(job.state)} size={24} />
                  <span>
                    <strong>{job.goal || "Encargo"}</strong>
                    <small>{t(STATE_LABELS[job.state] ?? "aiws.jobs")}</small>
                  </span>
                </button>
              </li>
            ))}
          </ul>
        )}
        {canLoadMore ? (
          <button
            type="button"
            className="ui-button ui-button--ghost"
            disabled={loadingMore}
            onClick={() => void more()}
          >
            {loadingMore ? "Cargando…" : "Conversaciones anteriores"}
          </button>
        ) : null}
        {historyError ? <p role="status">{historyError}</p> : null}
        <div className="assistant-history__settings">
          <Link to="/settings/general?section=ai">
            <Icon name="settings" size={18} />
            Preferencias de IA
          </Link>
          {owner ? (
            <details>
              <summary>Uso y resultados</summary>
              <AiMetricsCard organizationId={organizationId} />
            </details>
          ) : null}
        </div>
      </aside>
      <div className="assistant-room__main">
        <header className="assistant-room__header">
          <button
            type="button"
            className="ui-icon-button assistant-history-toggle"
            onClick={() => setHistoryOpen((open) => !open)}
            aria-expanded={historyOpen}
            aria-label="Ver conversaciones"
          >
            <Icon name="panel" />
          </button>
          <div className="assistant-room__identity">
            <Orb state={orbStateFor(current?.state ?? bound?.state)} size={30} />
            <span>
              <strong>DEKOPEN IA</strong>
              <small>
                {current
                  ? t(STATE_LABELS[current.state] ?? "aiws.jobs")
                  : "Diseñamos. Lo dejamos listo."}
              </small>
            </span>
          </div>
          <label className="assistant-context">
            <Icon name="projects" size={17} />
            <span className="visually-hidden">Obra para este encargo</span>
            <select
              aria-label="Obra para este encargo"
              value={typeof bound?.refs.project_id === "string" ? bound.refs.project_id : projectId}
              disabled={Boolean(selected || current)}
              onChange={(event) => {
                setProjectId(event.target.value);
                setEpoch((value) => value + 1);
              }}
            >
              <option value="">Mi empresa</option>
              {projects.data?.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.name || project.code}
                </option>
              ))}
            </select>
          </label>
          <button
            type="button"
            className="ui-icon-button"
            onClick={fresh}
            aria-label="Nuevo encargo"
            title="Nuevo encargo"
          >
            <Icon name="plus" />
          </button>
        </header>
        {(current ?? bound)?.outcomes?.length ? (
          <details className="assistant-audit" open={params.get("audit") === "1" || undefined}>
            <summary>Historial de decisiones</summary>
            <ol>
              {(current ?? bound)!.outcomes!.map((raw, index) => {
                const outcome = raw as {
                  action?: string;
                  created_at?: string;
                  turn_index?: number;
                  step_index?: number;
                };
                return (
                  <li key={index}>
                    <strong>
                      {(
                        {
                          applied: "Aplicado",
                          declined: "Descartado",
                          apply_failed: "No se pudo aplicar",
                          undone: "Deshecho",
                        } as Record<string, string>
                      )[outcome.action ?? ""] ?? "Decisión registrada"}
                    </strong>
                    <span>
                      Respuesta {(outcome.turn_index ?? 0) + 1} · propuesta{" "}
                      {(outcome.step_index ?? 0) + 1}
                    </span>
                    {outcome.created_at ? <time>{formatDateTime(outcome.created_at)}</time> : null}
                  </li>
                );
              })}
            </ol>
          </details>
        ) : null}
        {surface === "position" && refs.project_id && refs.position_id ? (
          <div className="assistant-room__context-note">
            <Icon name="window" size={17} />
            <span>Esta conversación trabaja sobre una ventana.</span>
            <Link
              to={`/projects/${refs.project_id}/positions/${refs.position_id}/edit${selected ? `?assistant_job=${selected}` : ""}`}
            >
              Abrir diseño
              <Icon name="arrow" size={15} />
            </Link>
          </div>
        ) : null}
        {selected && detail.isPending ? (
          <LoadingState label="Retomando la conversación" />
        ) : selected && detail.isError ? (
          <ErrorState
            title="No se pudo abrir la conversación"
            onRetry={() => void detail.refetch()}
          />
        ) : (
          <div
            className={`assistant-conversation${!selected && !current ? " assistant-conversation--new" : ""}`}
          >
            <AgentBody
              key={`${selected ?? "new"}:${projectId}:${epoch}`}
              organizationId={organizationId}
              userId={userId}
              surface={surface}
              refs={refs}
              jobId={selected}
              fresh={!selected}
              workspace
              draft={draft}
              onJob={onJob}
            />
            {!selected && !current ? (
              <div className="assistant-ideas" aria-label="Ideas para empezar">
                {IDEAS.map((idea) =>
                  idea.href ? (
                    <Link key={idea.title} to={idea.href} className="assistant-idea">
                      <Icon name={idea.icon} />
                      <strong>{idea.title}</strong>
                      <small>{idea.text}</small>
                      <Icon name="arrow" size={16} />
                    </Link>
                  ) : (
                    <button
                      type="button"
                      key={idea.title}
                      className="assistant-idea"
                      onClick={() =>
                        setDraft((old) => ({ text: idea.goal!, request: (old?.request ?? 0) + 1 }))
                      }
                    >
                      <Icon name={idea.icon} />
                      <strong>{idea.title}</strong>
                      <small>{idea.text}</small>
                      <Icon name="arrow" size={16} />
                    </button>
                  ),
                )}
              </div>
            ) : null}
            <p className="assistant-room__footnote">
              {current
                ? `Guardado · ${formatDateTime(current.updated_at)}`
                : "Tus preferencias ya forman parte del trabajo. Tú revisas el resultado."}
            </p>
          </div>
        )}
      </div>
    </section>
  );
}
