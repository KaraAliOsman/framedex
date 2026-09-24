import { type PropsWithChildren, useEffect } from "react";
import { NavLink, useLocation, useNavigate } from "react-router-dom";

import { t } from "../i18n/es-CL";

import { useAuthSession } from "../auth/AuthSessionProvider";
import { telemetry } from "../telemetry/telemetry";
import { useTheme } from "../theme/ThemeProvider";
import { CommandPalette } from "../features/commands/CommandPalette";

/** Information architecture: the rail is organized around the fenestration
 * job — work surfaces first, secondary records next, account/admin concerns
 * (billing, wallet, cost lists) nested inside Settings so they never compete
 * with the product's center of gravity. */
const navGroups = [
  {
    id: "work",
    items: [
      ["/dashboard", "nav.dashboard"],
      ["/projects", "nav.projects"],
      ["/production", "nav.production"],
      ["/purchasing", "nav.purchasing"],
      ["/catalogs/systems", "nav.systems"],
    ],
  },
  {
    id: "records",
    items: [
      ["/clients", "nav.clients"],
      ["/pricing/commercial", "pricing.calculate"],
    ],
  },
  {
    id: "account",
    items: [["/settings/general", "nav.settings"]],
  },
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
    if (to === "/catalogs/systems" || to === "/purchasing")
      return role === "OWNER" || role === "WORKSHOP_MANAGER";
    if (to === "/pricing/commercial") return role === "OWNER" || role === "ESTIMATOR";
    if (to === "/clients")
      return role === "OWNER" || role === "ESTIMATOR" || role === "WORKSHOP_MANAGER";
    if (to === "/production")
      return role === "OWNER" || role === "WORKSHOP_MANAGER" || role === "INSTALLER";
    return true;
  }

  const navItems = navGroups.flatMap((group) =>
    group.items.filter(([to]) => navigationAllowed(to)).map(([to, label]) => ({ to, label })),
  );

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
        {navGroups.map((group, index) => {
          const items = group.items.filter(([to]) => navigationAllowed(to));
          if (items.length === 0) return null;
          return (
            <div
              key={group.id}
              className={`tool-rail__group${group.id === "account" ? " tool-rail__group--account" : ""}`}
            >
              {index > 0 && <span className="tool-rail__divider" aria-hidden />}
              {items.map(([to, label]) => (
                <NavLink key={to} to={to} title={t(label)} aria-label={t(label)}>
                  {t(label)}
                </NavLink>
              ))}
            </div>
          );
        })}
      </nav>
      <main className="workspace">{children}</main>
      <CommandPalette
        navItems={navItems.map(({ to, label }) => ({ to, label: t(label) }))}
        onNavigate={(to) => navigate(to)}
      />
      <footer className="status-bar">
        <span>{t("shell.engineStatus")}</span>
        <span>{t("shell.apiStatus")}</span>
      </footer>
    </div>
  );
}
