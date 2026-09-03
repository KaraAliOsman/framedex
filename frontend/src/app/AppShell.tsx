import { type PropsWithChildren, useEffect } from "react";
import { NavLink, useLocation } from "react-router-dom";

import { t } from "../i18n/es-CL";

import { useAuthSession } from "../auth/AuthSessionProvider";
import { telemetry } from "../telemetry/telemetry";
import { useTheme } from "../theme/ThemeProvider";

const navigation = [
  ["/dashboard", "nav.dashboard"],
  ["/projects", "nav.projects"],
  ["/catalogs/systems", "nav.systems"],
  ["/settings/general", "nav.settings"],
] as const;

export function AppShell({ children }: PropsWithChildren): JSX.Element {
  const auth = useAuthSession();
  const { theme, toggleTheme } = useTheme();
  const location = useLocation();
  useEffect(() => {
    telemetry.capture("shell_route_viewed", { route_name: location.pathname });
  }, [location.pathname]);

  return (
    <div className="app-shell" data-testid="app-shell">
      <header className="app-ribbon">
        <span className="brand">{t("app.brand")}</span>
        <span className="context-title">{auth.me?.active_organization?.name ?? t("org.none")}</span>
        <button type="button" onClick={toggleTheme} aria-label={t("theme.toggle")}>
          {t(theme === "light" ? "theme.toDark" : "theme.toLight")}
        </button>
        <button type="button" onClick={() => void auth.signOut()}>
          {t("auth.signOut")}
        </button>
      </header>
      <nav className="tool-rail" aria-label={t("shell.navigation")}>
        {navigation.map(([to, label]) => (
          <NavLink key={to} to={to} title={t(label)} aria-label={t(label)}>
            {t(label).slice(0, 1)}
          </NavLink>
        ))}
      </nav>
      <main className="workspace">{children}</main>
      <aside className="context-panel">
        <p className="panel-label">{t("shell.organization")}</p>
        <strong>{auth.me?.active_organization?.name}</strong>
        <span>{auth.me?.active_organization?.role}</span>
      </aside>
      <footer className="status-bar">
        <span>{t("shell.engineStatus")}</span>
        <span>{t("shell.apiStatus")}</span>
      </footer>
    </div>
  );
}
