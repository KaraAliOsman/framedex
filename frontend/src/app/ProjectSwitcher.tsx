import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";

import { ApiError } from "../api/apiMutator";
import { projectsList } from "../api/generated/dekopen";
import type { ProjectResponse } from "../api/generated/models";
import { useAuthSession } from "../auth/AuthSessionProvider";
import { t } from "../i18n/es-CL";
import { useDismiss } from "./shellUtils";

/** Jump between recent projects without leaving the project context. Only
 * rendered inside /projects/:id — everywhere else the rail already offers
 * the full list. Fetch is lazy on first open. */
export function ProjectSwitcher(): JSX.Element | null {
  const org = useAuthSession().me?.active_organization;
  const location = useLocation();
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<ProjectResponse[] | null>(null);
  const [failed, setFailed] = useState(false);
  const rootRef = useDismiss<HTMLDivElement>(open, () => setOpen(false));

  const parts = location.pathname.split("/").filter(Boolean);
  const projectId = parts[0] === "projects" && parts[1] && parts[1] !== "demo" ? parts[1] : null;

  useEffect(() => {
    if (!open || !org || items !== null || failed) return;
    projectsList({ headers: { "X-Organization-ID": org.id } })
      .then((response) => {
        if (response.status !== 200) throw new ApiError(response.status, response.data);
        setItems(response.data.items.slice(0, 8));
      })
      .catch(() => setFailed(true));
  }, [open, org, items, failed]);

  if (!org || !projectId) return null;

  const candidates = (items ?? []).filter((item) => item.id !== projectId);
  return (
    <div className="project-switcher" ref={rootRef}>
      <button
        type="button"
        className="topbar-button"
        aria-haspopup="menu"
        aria-expanded={open || undefined}
        onClick={() => setOpen((value) => !value)}
      >
        {t("shell.switchProject")}
        <span aria-hidden className="topbar-button__chevron">
          ▾
        </span>
      </button>
      {open && (
        <div
          className="shell-menu shell-menu--right"
          role="menu"
          aria-label={t("shell.switchProject")}
        >
          <p className="shell-menu__title">{t("shell.recentProjects")}</p>
          {items === null && !failed ? (
            <p className="shell-menu__meta">{t("projects.loading")}</p>
          ) : failed ? (
            <p className="shell-menu__meta" role="alert">
              {t("projects.uncertain")}
            </p>
          ) : candidates.length === 0 ? (
            <p className="shell-menu__meta">{t("shell.noOtherProjects")}</p>
          ) : (
            <ul>
              {candidates.map((item) => (
                <li key={item.id}>
                  <Link
                    role="menuitem"
                    className="shell-menu__item"
                    to={`/projects/${item.id}`}
                    onClick={() => setOpen(false)}
                  >
                    <span>
                      {item.code} · {item.name}
                    </span>
                    <span className="shell-menu__meta">{item.client_name}</span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
