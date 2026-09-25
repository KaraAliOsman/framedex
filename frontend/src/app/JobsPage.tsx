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

interface JobFailure {
  /** The wrapper code — `job_permanent_error` wraps the domain code. */
  code: string;
  /** The domain failure — `error.detail` for permanent wraps, else the code. */
  detail: string;
  permanent: boolean;
}

function jobFailure(error: JobRun["error"]): JobFailure | null {
  if (error === null || error === undefined) return null;
  if (typeof error === "object" && "code" in (error as Record<string, unknown>)) {
    const record = error as Record<string, unknown>;
    const code = String(record.code);
    return {
      code,
      detail: String(record.detail ?? code),
      permanent: code === "job_permanent_error",
    };
  }
  return { code: "", detail: String(error), permanent: false };
}

/** Backend failure codes grouped into operator-facing recovery language; the
 * raw code stays visible as a diagnostic tail, not as the message. */
function jobErrorKey(code: string): TranslationKey {
  if (code.endsWith("_not_found")) return "jobs.fail.notFound";
  if (code.includes("permission") || code.includes("access_denied")) return "jobs.fail.permission";
  if (code.startsWith("document_storage_")) return "jobs.fail.storage";
  if (code.includes("hash_mismatch") || code.includes("stale")) return "jobs.fail.stale";
  if (
    code.startsWith("ai_") ||
    code.includes("provider") ||
    code.includes("timeout") ||
    code.includes("unavailable")
  )
    return "jobs.fail.provider";
  if (code.startsWith("invalid_") || code.endsWith("_invalid") || code.includes("required"))
    return "jobs.fail.invalid";
  return "jobs.fail.generic";
}

/** Permanent categories where re-running the same payload cannot help — the
 * recovery is a different action (fix access / re-emit), so no retry button. */
const NON_RETRYABLE: ReadonlySet<TranslationKey> = new Set([
  "jobs.fail.notFound",
  "jobs.fail.permission",
]);

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
          {items.map((job) => {
            const failure = jobFailure(job.error);
            const failureKey = failure ? jobErrorKey(failure.detail) : null;
            const canRetry =
              TERMINAL_RETRYABLE.has(job.state) &&
              !(failure?.permanent && failureKey && NON_RETRYABLE.has(failureKey));
            return (
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
                {job.state === "FAILED" && failure !== null && failureKey !== null && (
                  <p className="job-row-error">
                    {t(failureKey)} <code className="job-row-code">{failure.detail}</code>
                  </p>
                )}
                {canRetry && (
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
    </section>
  );
}
