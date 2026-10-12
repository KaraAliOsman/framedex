import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { ApiError } from "../api/apiMutator";
import { jobsList, jobsRetry } from "../api/generated/dekopen";
import type { JobRun } from "../api/generated/models";
import { useAuthSession } from "../auth/AuthSessionProvider";
import { jobErrorKey } from "../features/jobs/jobError";
import { formatDateTime } from "../format";
import { EmptyState, PageHeader, StatusChip, LoadingState, ErrorState, DeniedState } from "../ui";
import { t, tDynamic, type TranslationKey } from "../i18n/es-CL";
import { AiWorkList } from "../features/assistant/AiWorkList";
import { AI_CAPABILITIES } from "../features/assistant/providerLabels";

const STATE_KEYS: Record<string, TranslationKey> = {
  QUEUED: "jobs.state.QUEUED",
  RUNNING: "jobs.state.RUNNING",
  SUCCEEDED: "jobs.state.SUCCEEDED",
  FAILED: "jobs.state.FAILED",
  CANCELED: "jobs.state.CANCELED",
};

function duration(value: number | null | undefined): string {
  if (value == null) return "Sin dato: aún no comenzó";
  const seconds = Math.floor(value / 1000);
  return seconds >= 60 ? `${Math.floor(seconds / 60)} min ${seconds % 60} s` : `${seconds} s`;
}

function typeLabel(type: string): string {
  return tDynamic("jobs.type", type);
}

interface JobFailure {
  /** The wrapper code — `job_permanent_error` wraps the domain code. */
  code: string;
  /** The domain failure — `error.detail` for permanent wraps, else the code. */
  detail: string;
}

function jobFailure(error: JobRun["error"]): JobFailure | null {
  if (error === null || error === undefined) return null;
  if (typeof error === "object" && "code" in (error as Record<string, unknown>)) {
    const record = error as Record<string, unknown>;
    const code = String(record.code);
    return { code, detail: String(record.detail ?? code) };
  }
  return { code: "", detail: String(error) };
}

/** Background work made visible: what ran, what's running, what failed —
 * with the recovery action (reintentar) next to the failure it fixes.
 * The backend declares retry eligibility and reauthorizes each attempt. */
const PAGE_SIZE = 100;

export function JobsPage(): JSX.Element {
  const org = useAuthSession().me?.active_organization;
  const [params, setParams] = useSearchParams();
  const [notice, setNotice] = useState("");
  const client = useQueryClient();
  const stateFilter = params.get("state") ?? "";
  const capabilityFilter = params.get("capability") ?? "";
  const [pages, setPages] = useState(1);

  const query = useQuery<JobRun[]>({
    queryKey: ["jobs", "list", org?.id, stateFilter, pages],
    enabled: org !== undefined && !capabilityFilter,
    // A running job is a living row — poll fast while anything can still
    // move; idle keeps a slow beat so jobs started elsewhere still appear.
    refetchInterval: (result) =>
      (result.state.data ?? []).some((job) => job.state === "QUEUED" || job.state === "RUNNING")
        ? 4_000
        : 60_000,
    queryFn: async ({ signal }) => {
      // Older failures stay reachable: all loaded pages refresh in parallel —
      // a 4s poll must not run N serial round-trips.
      const responses = await Promise.all(
        Array.from({ length: pages }, (_, page) =>
          jobsList(
            {
              limit: PAGE_SIZE,
              offset: page * PAGE_SIZE,
              state: stateFilter === "" ? undefined : (stateFilter as never),
            },
            { signal, headers: { "X-Organization-ID": org!.id } },
          ),
        ),
      );
      const all: JobRun[] = [];
      for (const response of responses) {
        if (response.status !== 200) {
          throw new ApiError(response.status, response.data);
        }
        all.push(...response.data);
      }
      return all;
    },
  });

  const retry = useMutation({
    mutationFn: async (jobId: string) => {
      const response = await jobsRetry(jobId, {
        headers: { "X-Organization-ID": org!.id },
      });
      if (response.status !== 200) {
        throw new ApiError(response.status, response.data);
      }
      return response.data;
    },
    onSuccess: () => {
      setNotice(t("jobs.retryQueued"));
      void client.invalidateQueries({ queryKey: ["jobs", "list"] });
      // The shell badge counts failed jobs — refetch after requeueing.
      void client.invalidateQueries({ queryKey: ["shell", "attention"] });
    },
    onError: () => setNotice(t("jobs.retryFailed")),
  });

  const items = query.data ?? [];
  const hasMore = items.length === pages * PAGE_SIZE;
  return (
    <section className="dashboard jobs-page" aria-labelledby="page-title">
      <PageHeader
        actions={
          <div className="ai-work-filters">
            <label className="ui-field jobs-filter">
              <span className="ui-field__label">Capacidad</span>
              <select
                className="ui-field__input"
                value={capabilityFilter}
                onChange={(event) => {
                  const next = new URLSearchParams(params);
                  if (event.target.value) next.set("capability", event.target.value);
                  else next.delete("capability");
                  setPages(1);
                  setParams(next, { replace: true });
                }}
              >
                <option value="">Todos los trabajos</option>
                <option value="all_ai">Todas las llamadas de IA</option>
                {["design_assist", "agent", "context_assist", "catalog_import"].map(
                  (capability) => (
                    <option key={capability} value={capability}>
                      {AI_CAPABILITIES[capability]}
                    </option>
                  ),
                )}
              </select>
            </label>
            <label className="ui-field jobs-filter">
              <span className="ui-field__label">{t("jobs.filter.state")}</span>
              <select
                className="ui-field__input"
                value={stateFilter}
                onChange={(event) => {
                  const next = new URLSearchParams(params);
                  if (event.target.value === "") next.delete("state");
                  else next.set("state", event.target.value);
                  setParams(next, { replace: true });
                  setPages(1);
                }}
              >
                <option value="">{t("jobs.filter.all")}</option>
                {Object.keys(STATE_KEYS).map((state) => (
                  <option key={state} value={state}>
                    {t(STATE_KEYS[state] ?? "jobs.state.QUEUED")}
                  </option>
                ))}
              </select>
            </label>
          </div>
        }
        context={t("jobs.subtitle")}
        headingId="page-title"
        title={t("jobs.title")}
      />

      {notice !== "" && <p role="status">{notice}</p>}
      {capabilityFilter ? (
        <AiWorkList capability={capabilityFilter} state={stateFilter} />
      ) : query.isPending ? (
        <LoadingState label="Cargando trabajos" />
      ) : query.isError ? (
        query.error instanceof ApiError && query.error.status === 403 ? (
          <DeniedState reason="Pide al dueño, a un estimador o al jefe de taller que revise el trabajo." />
        ) : (
          <ErrorState title={t("jobs.error")} onRetry={() => void query.refetch()} />
        )
      ) : items.length === 0 ? (
        <EmptyState title={t("jobs.empty")} />
      ) : (
        <ul className="jobs-list">
          {items.map((job) => {
            const queueState = job.state;
            const failure = jobFailure(job.error);
            const failureKey = failure ? jobErrorKey(failure.detail) : null;
            return (
              <li key={job.id} className="job-row" data-state={job.state.toLowerCase()}>
                <div className="job-row-main">
                  <strong>{typeLabel(job.type)}</strong>
                  <StatusChip status={queueState} />
                  {job.ai_job_id ? (
                    <Link
                      className="ui-button ui-button--small ui-button--ghost"
                      to={`/assistant?job=${job.ai_job_id}`}
                    >
                      {t("jobs.openAssistant")}
                    </Link>
                  ) : null}
                </div>
                <p className="job-row-object">
                  {job.context_url ? (
                    <Link to={job.context_url}>{job.context_label}</Link>
                  ) : (
                    (job.context_label ?? "Trabajo de organización")
                  )}
                </p>
                <div className="job-row-meta">
                  <span>{job.actor_label ?? "Usuario no disponible"}</span>
                  <span>Duración: {duration(job.duration_ms)}</span>
                  <span>
                    {t("jobs.attempt")
                      .replace("{attempt}", String(job.attempt))
                      .replace("{max}", String(job.max_attempts))}
                  </span>
                  <time dateTime={job.created_at}>{formatDateTime(job.created_at)}</time>
                </div>
                <p>{job.result_label}</p>
                {job.state === "FAILED" && failure !== null && failureKey !== null && (
                  <p className="job-row-error">{t(failureKey)}</p>
                )}
                {job.state === "FAILED" && failure && /^[a-z0-9_]+$/.test(failure.detail) && (
                  <details className="ui-tech">
                    <summary>Detalles técnicos</summary>
                    <code>{failure.detail}</code>
                  </details>
                )}
                {job.can_retry === true && (
                  <button
                    type="button"
                    className="ui-button ui-button--small"
                    disabled={retry.isPending}
                    onClick={() => {
                      setNotice("");
                      retry.mutate(job.id);
                    }}
                  >
                    {retry.isPending ? t("jobs.retrying") : t("jobs.retry")}
                  </button>
                )}
              </li>
            );
          })}
        </ul>
      )}
      {!capabilityFilter && !query.isPending && !query.isError && hasMore && (
        <button
          type="button"
          className="ui-button"
          disabled={query.isFetching}
          onClick={() => setPages((value) => value + 1)}
        >
          {query.isFetching ? t("dashboard.attentionLoading") : t("jobs.loadMore")}
        </button>
      )}
    </section>
  );
}
