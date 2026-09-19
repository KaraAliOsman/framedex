import { Link } from "react-router-dom";

import { t } from "../i18n/es-CL";

export function DashboardPage(): JSX.Element {
  return (
    <section className="placeholder" aria-labelledby="page-title">
      <h1 id="page-title">{t("page.dashboard")}</h1>
      <p>{t("page.dashboardDescription")}</p>
      <div className="projects-actions">
        <Link className="primary-action" to="/projects">
          {t("projects.title")}
        </Link>
        <Link to="/projects/demo/positions/g1/edit">{t("canvas.openDemo")}</Link>
      </div>
    </section>
  );
}
