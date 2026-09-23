import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { ApiError } from "../api/apiMutator";
import { projectsList } from "../api/generated/dekopen";
import type { ProjectResponse } from "../api/generated/models";
import { useAuthSession } from "../auth/AuthSessionProvider";
import { t, type TranslationKey } from "../i18n/es-CL";

const statuses: Record<ProjectResponse["status"], TranslationKey> = {
  DRAFT: "projects.draft",
  QUOTED: "projects.quoted",
  APPROVED: "projects.approved",
  IN_PRODUCTION: "projects.production",
  COMPLETED: "projects.completed",
  CANCELLED: "projects.cancelled",
};

export function DashboardPage(): JSX.Element {
  const auth = useAuthSession();
  const org = auth.me?.active_organization;
  const query = useQuery<ProjectResponse[]>({
    queryKey: ["dashboard", "projects", org?.id],
    enabled: org !== undefined,
    queryFn: async ({ signal }) => {
      const response = await projectsList({
        signal,
        headers: { "X-Organization-ID": org!.id },
      });
      if (response.status !== 200) {
        throw new ApiError(response.status, response.data);
      }
      return response.data.items;
    },
  });

  const items = query.data ?? [];
  const recent = [...items].sort((a, b) => b.updated_at.localeCompare(a.updated_at)).slice(0, 8);
  const next = recent.find((item) => item.status === "DRAFT") ?? null;
  const active = items.filter((item) => item.status === "DRAFT" || item.status === "QUOTED");
  const inProduction = items.filter(
    (item) => item.status === "APPROVED" || item.status === "IN_PRODUCTION",
  );
  const canWrite = org?.role === "OWNER" || org?.role === "ESTIMATOR";

  return (
    <section className="dashboard" aria-labelledby="page-title">
      <header className="dashboard-head">
        <div>
          <h1 id="page-title">{t("page.dashboard")}</h1>
          <p className="dashboard-sub">{org?.name ?? t("org.none")}</p>
        </div>
        {canWrite && (
          <Link className="primary-action" to="/projects">
            {t("projects.create")}
          </Link>
        )}
      </header>

      {query.isError && <p role="alert">{t("projects.uncertain")}</p>}

      {next && (
        <Link to={`/projects/${next.id}`} className="dashboard-continue">
          <span className="eyebrow">{t("dashboard.continue")}</span>
          <span className="dashboard-continue-name">
            {next.code} · {next.name}
          </span>
          <span className="dashboard-continue-meta">
            {next.client_name} ·{" "}
            <time dateTime={next.updated_at}>
              {new Date(next.updated_at).toLocaleString("es-CL")}
            </time>
          </span>
          <span className="dashboard-continue-cta">{t("dashboard.resume")}</span>
        </Link>
      )}

      <div className="dashboard-cards">
        <div className="metric-card">
          <span className="eyebrow">{t("dashboard.inProgress")}</span>
          <strong>{active.length}</strong>
        </div>
        <div className="metric-card">
          <span className="eyebrow">{t("dashboard.production")}</span>
          <strong>{inProduction.length}</strong>
        </div>
        <div className="metric-card">
          <span className="eyebrow">{t("projects.title")}</span>
          <strong>{items.length}</strong>
        </div>
      </div>

      {query.isPending ? (
        <p role="status">{t("projects.loading")}</p>
      ) : items.length === 0 ? (
        <div className="dashboard-empty">
          <p>{t("dashboard.empty")}</p>
          {canWrite && (
            <Link className="primary-action" to="/projects">
              {t("dashboard.emptyCta")}
            </Link>
          )}
        </div>
      ) : (
        <div className="dashboard-list">
          <div className="dashboard-list-head">
            <h2 className="eyebrow">{t("dashboard.recent")}</h2>
            <Link to="/projects">{t("dashboard.viewAll")}</Link>
          </div>
          <ul>
            {recent.map((item) => (
              <li key={item.id}>
                <Link to={`/projects/${item.id}`} className="dashboard-row">
                  <span className="dashboard-row-code">{item.code}</span>
                  <span className="dashboard-row-name">{item.name}</span>
                  <span className="dashboard-row-client">{item.client_name}</span>
                  <span className="status-chip" data-status={item.status.toLowerCase()}>
                    {t(statuses[item.status])}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
