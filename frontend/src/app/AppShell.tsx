import { type PropsWithChildren, useEffect } from "react";
import { NavLink, useLocation, useNavigate } from "react-router-dom";

import { t } from "../i18n/es-CL";

import { useAuthSession } from "../auth/AuthSessionProvider";
import { telemetry } from "../telemetry/telemetry";
import { useTheme } from "../theme/ThemeProvider";
import { CommandPalette } from "../features/commands/CommandPalette";

const navigation = [
  ["/settings/wallet", "wallet.title"],
  ["/settings/billing", "billing.title"],
  ["/dashboard", "nav.dashboard"],
  ["/projects", "nav.projects"],
  ["/clients", "nav.clients"],
  ["/catalogs/systems", "nav.systems"],
  ["/settings/general", "nav.settings"],
  ["/pricing/cost-lists", "pricing.title"],
  ["/pricing/commercial", "pricing.calculate"],
  ["/purchasing", "nav.purchasing"],
  ["/production", "nav.production"],
] as const;

export function AppShell({ children }: PropsWithChildren): JSX.Element {
  const auth = useAuthSession();
  const { theme, toggleTheme } = useTheme();
  const location = useLocation();
  const navigate = useNavigate();
  useEffect(() => {
    telemetry.capture("shell_route_viewed", { route_name: location.pathname });
  }, [location.pathname]);
  const role = auth.me?.active_organization?.role;
  function navigationAllowed(to: string): boolean {
    if (to === "/pricing/cost-lists" || to === "/settings/wallet" || to === "/settings/billing")
      return role === "OWNER";
    if (to === "/catalogs/systems") return role === "OWNER" || role === "WORKSHOP_MANAGER";
    if (to === "/pricing/commercial") return role === "OWNER" || role === "ESTIMATOR";
    if (to === "/purchasing") return role === "OWNER" || role === "WORKSHOP_MANAGER";
    if (to === "/production")
      return role === "OWNER" || role === "WORKSHOP_MANAGER" || role === "INSTALLER";
    return true;
  }

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
        {navigation
          .filter(([to]) => navigationAllowed(to))
          .map(([to, label]) => (
            <NavLink key={to} to={to} title={t(label)} aria-label={t(label)}>
              {t(label)}
            </NavLink>
          ))}
      </nav>
      <main className="workspace">{children}</main>
      <CommandPalette
        navItems={navigation
          .filter(([to]) => navigationAllowed(to))
          .map(([to, label]) => ({ to, label: t(label) }))}
        onNavigate={(to) => navigate(to)}
      />
      <footer className="status-bar">
        <span>{t("shell.engineStatus")}</span>
        <span>{t("shell.apiStatus")}</span>
      </footer>
    </div>
  );
}
