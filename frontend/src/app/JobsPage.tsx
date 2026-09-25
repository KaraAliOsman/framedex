import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useSearchParams } from "react-router-dom";

import { ApiError } from "../api/apiMutator";
import { jobsList, jobsRetry } from "../api/generated/dekopen";
import type { JobRun } from "../api/generated/models";
import { useAuthSession } from "../auth/AuthSessionProvider";
import { t, tDynamic, type TranslationKey } from "../i18n/es-CL";

const STATE_KEYS: Record<string, TranslationKey> = {
  QUEUED: "jobs.state.QUEUED",
  RUNNING: "jobs.state.RUNNING",
  SUCCEEDED: "jobs.state.SUCCEEDED",
  FAILED: "jobs.state.FAILED",
  CANCELED: "jobs.state.CANCELED",
};

const TERMINAL_RETRYABLE = new Set(["FAILED", "CANCELED"]);

function typeLabel(type: string): string {
  return tDynamic("jobs.type", type);
}

function jobError(error: JobRun["error"]): string {
  if (error === null || error === undefined) return "";
  if (typeof error === "object" && "code" in (error as Record<string, unknown>)) {
    return String((error as Record<string, unknown>).code);
  }
  return String(error);
}

/** Background work made visible: what ran, what's running, what failed —
 * with the recovery action (reintentar) next to the failure it fixes. */
export function JobsPage(): JSX.Element {
  const org = useAuthSession().me?.active_organization;
  const [params, setParams] = useSearchParams();
  const [notice, setNotice] = useState("");
  const client = useQueryClient();
  const stateFilter = params.get("state") ?? "";

  const query = useQuery<JobRun[]>({
    queryKey: ["jobs", "list", org?.id, stateFilter],
    enabled: org !== undefined,
    // A running job is a living row — poll while anything can still move.
    refetchInterval: (result) =>
      (result.state.data ?? []).some((job) => job.state === "QUEUED" || job.state === "RUNNING")
        ? 4_000
        : false,
    queryFn: async ({ signal }) => {
      const response = await jobsList(
        { limit: 100, state: stateFilter === "" ? undefined : (stateFilter as never) },
        { signal, headers: { "X-Organization-ID": org!.id } },
      );
      if (response.status !== 200) {
        throw new ApiError(response.status, response.data);
      }
      return response.data;
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
  return (
    <section className="dashboard" aria-labelledby="page-title">
      <header className="dashboard-head">
        <div>
          <h1 id="page-title">{t("jobs.title")}</h1>
          <p className="dashboard-sub">{t("jobs.subtitle")}</p>
        </div>
        <label className="ui-field jobs-filter">
          <span className="ui-field__label">{t("jobs.filter.state")}</span>
          <select
            value={stateFilter}
            onChange={(event) => {
              const next = new URLSearchParams(params);
              if (event.target.value === "") next.delete("state");
              else next.set("state", event.target.value);
              setParams(next, { replace: true });
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
      </header>

      {notice !== "" && <p role="status">{notice}</p>}
      {query.isPending ? (
        <p role="status">{t("dashboard.attentionLoading")}</p>
      ) : query.isError ? (
        <p role="alert">{t("jobs.error")}</p>
      ) : items.length === 0 ? (
        <div className="dashboard-empty">
          <p>{t("jobs.empty")}</p>
        </div>
      ) : (
        <ul className="jobs-list">
          {items.map((job) => (
            <li key={job.id} className="job-row" data-state={job.state.toLowerCase()}>
              <div className="job-row-main">
                <strong>{typeLabel(job.type)}</strong>
                <span className="status-chip" data-status={job.state.toLowerCase()}>
                  {t(STATE_KEYS[job.state] ?? "jobs.state.QUEUED")}
                </span>
              </div>
              <div className="job-row-meta">
                <span>
                  {t("jobs.attempt")
                    .replace("{attempt}", String(job.attempt))
                    .replace("{max}", String(job.max_attempts))}
                </span>
                <span>{t("jobs.progress").replace("{percent}", job.progress)}</span>
                <time dateTime={job.created_at}>
                  {new Date(job.created_at).toLocaleString("es-CL")}
                </time>
              </div>
              {job.state === "FAILED" && jobError(job.error) !== "" && (
                <p className="job-row-error">{jobError(job.error)}</p>
              )}
              {TERMINAL_RETRYABLE.has(job.state) && (
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
          ))}
        </ul>
      )}
    </section>
  );
}
