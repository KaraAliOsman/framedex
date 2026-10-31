import { type PropsWithChildren, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Link, NavLink, useLocation, useNavigate } from "react-router-dom";

import { t } from "../i18n/es-CL";
import { Wordmark, BrandMark } from "../brand/Brand";
import { useAuthSession } from "../auth/AuthSessionProvider";
import { MOD_K_HINT } from "../platform";
import { telemetry } from "../telemetry/telemetry";
import { CommandPalette } from "../features/commands/CommandPalette";
import { AiModeBadge } from "../features/assistant/AiModeBadge";
import { Companion } from "../features/assistant/Companion";
import { CopilotWindow } from "../features/assistant/CopilotWindow";
import { useCopilotStatus } from "../features/assistant/copilotStatus";
import { AssistantSurfaceProvider } from "../features/assistant/assistantContext";
import { useCapabilities } from "../features/plans/useCapabilities";
import { CopilotProvider } from "../features/assistant/copilotBridge";
import { Icon } from "../ui/Icon";
import { Popover } from "../ui/Overlays";
import { AttentionBell } from "./AttentionBell";
import { OrgSwitcher } from "./OrgSwitcher";
import { ShellCrumbs, crumbsFor, useProjectName } from "./ShellCrumbs";
import { ShellLeafContext } from "./shellLeaf";
import { roleLabel } from "./shellUtils";
import { areaFor, homeFor, navigationFor, paletteNavigationFor } from "./navigation";
import { ShortcutHelp } from "./ShortcutHelp";
import { obraVistaUnica } from "./productFeatures";
import { useApplyInterface, useInterfacePreferences } from "./interfacePreferences";

/** The product shell (constitution §5.1): Hoy, Obras, Taller, Catálogo and Empresa,
 * a 56 px top bar with search, notices and the assistant, and the area's own
 * sections as tabs on its list pages. Detail pages keep the full height. */
export function AppShell({ children }: PropsWithChildren): JSX.Element {
  const auth = useAuthSession();
  const location = useLocation();
  const navigate = useNavigate();
  const org = auth.me?.active_organization;
  const role = org?.role;
  const look = useInterfacePreferences(org?.id);
  useApplyInterface(look.preferences);
  const workshop =
    look.preferences.density === "workshop" ||
    location.pathname.startsWith("/production") ||
    role === "OPERATOR" ||
    role === "INSTALLER";
  const [leaf, setLeafState] = useState<string | null>(null);
  const setLeaf = useCallback((label: string | null) => setLeafState(label), []);
  const leafContext = useMemo(() => ({ leaf, setLeaf }), [leaf, setLeaf]);
  const [paletteRequest, setPaletteRequest] = useState(0);
  const [assistantRequest, setAssistantRequest] = useState(0);
  const [railOpen, setRailOpen] = useState(false);
  const railRef = useRef<HTMLElement>(null);
  const toggleRef = useRef<HTMLButtonElement>(null);
  const collapsed = look.preferences.rail_collapsed;

  // The drawer only exists below the tablet breakpoint; it closes on route
  // change and on Escape, and traps focus while open.
  useEffect(() => setRailOpen(false), [location.pathname]);
  useEffect(() => {
    function onKey(event: KeyboardEvent): void {
      if (event.key === "Escape") setRailOpen(false);
    }
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, []);
  useEffect(() => {
    if (!railOpen) return;
    const panel = railRef.current;
    const focusables = () =>
      Array.from(
        panel?.querySelectorAll<HTMLElement>("a[href], button:not([disabled])") ?? [],
      ).filter((node) => node.getClientRects().length > 0);
    focusables()[0]?.focus();
    const key = (event: KeyboardEvent) => {
      if (event.key !== "Tab") return;
      const nodes = focusables(),
        first = nodes[0],
        last = nodes[nodes.length - 1];
      if (!first || !last) return;
      const outside = !panel?.contains(document.activeElement);
      if (
        event.shiftKey
          ? document.activeElement === first || outside
          : document.activeElement === last || outside
      ) {
        event.preventDefault();
        (event.shiftKey ? last : first).focus();
      }
    };
    const dismiss = () => setRailOpen(false);
    document.addEventListener("keydown", key);
    window.addEventListener("dekopen:shell-overlay", dismiss);
    return () => {
      document.removeEventListener("keydown", key);
      window.removeEventListener("dekopen:shell-overlay", dismiss);
      toggleRef.current?.focus();
    };
  }, [railOpen]);

  useEffect(() => {
    telemetry.capture("shell_route_viewed", { route_name: location.pathname });
  }, [location.pathname]);
  useEffect(() => {
    const open = () => setAssistantRequest((value) => value + 1);
    window.addEventListener("dekopen:assistant-open", open);
    return () => window.removeEventListener("dekopen:assistant-open", open);
  }, []);

  // The copilot exists only for organizations whose plan includes the AI core
  // (server resolution). The manual plan mounts no button, presence, popup or
  // polling — the quoter is complete without it.
  const capabilities = useCapabilities();
  const copilotStatus = useCopilotStatus();
  const copilotPose = copilotStatus.state;
  const canUseAssistant =
    capabilities.aiEntitled &&
    (role === "OWNER" || role === "ESTIMATOR" || role === "WORKSHOP_MANAGER");
  const parts = location.pathname.split("/").filter(Boolean);
  const projectId = parts[0] === "projects" && parts[1] !== undefined ? parts[1] : null;
  const isStudio = parts[0] === "projects" && parts[2] === "positions" && parts.length >= 4;
  const isWorkbench =
    obraVistaUnica() &&
    projectId !== null &&
    (role === "OWNER" || role === "ESTIMATOR") &&
    !new URLSearchParams(location.search).get("section");
  const compact = isStudio || isWorkbench || collapsed;
  const areas = navigationFor(role);
  const everyday = areas.filter((area) => area.id !== "company");
  const company = areas.find((area) => area.id === "company");
  const activeArea = areaFor(location.pathname, role);
  const tabs =
    activeArea &&
    activeArea.sections.length > 1 &&
    activeArea.sections.some((section) => section.to === location.pathname)
      ? activeArea.sections
      : null;
  const projectName = useProjectName(projectId !== "demo" ? projectId : null);

  // Browser tab title tracks the same crumbs the shell renders.
  useEffect(() => {
    const crumbs = crumbsFor(location.pathname, projectName, leaf);
    const head = crumbs
      .slice(-2)
      .map((crumb) => crumb.label)
      .join(" · ");
    document.title = head ? `${head} · DEKOPEN` : "DEKOPEN";
  }, [location.pathname, projectName, leaf]);

  const paletteItems = paletteNavigationFor(role).map((section) => ({
    to: section.to,
    label: t(section.label),
  }));

  return (
    <ShellLeafContext.Provider value={leafContext}>
      <AssistantSurfaceProvider>
        <CopilotProvider available={canUseAssistant}>
          <div
            className={`app-shell${railOpen ? " rail-open" : ""}${compact ? " rail-collapsed" : ""}`}
            data-studio={isStudio || undefined}
            data-density={workshop ? "workshop" : "office"}
            data-testid="app-shell"
          >
            <a href="#workspace-main" className="skip-link">
              {t("shell.skipToContent")}
            </a>
            <button
              type="button"
              className="rail-scrim"
              aria-label="Cerrar navegación"
              aria-hidden={!railOpen}
              tabIndex={railOpen ? 0 : -1}
              onClick={() => setRailOpen(false)}
            />
            <aside
              className="app-rail"
              ref={railRef}
              role={railOpen ? "dialog" : undefined}
              aria-modal={railOpen || undefined}
              aria-label="Navegación"
            >
              <Link className="app-rail__brand" to={homeFor(role)} aria-label="DEKOPEN · inicio">
                <span className="rail-brand-full">
                  <Wordmark width={116} />
                </span>
                <span className="rail-brand-compact">
                  <BrandMark size={26} title="DEKOPEN" />
                </span>
              </Link>
              <nav className="app-rail__nav" aria-label={t("shell.navigation")}>
                {everyday.map((area) => (
                  <NavLink
                    className={() => `rail-item${activeArea?.id === area.id ? " active" : ""}`}
                    key={area.id}
                    to={area.to}
                    title={t(area.label)}
                    aria-current={activeArea?.id === area.id ? "page" : undefined}
                  >
                    <Icon name={area.icon} className="rail-item__icon" />
                    <span>{t(area.label)}</span>
                  </NavLink>
                ))}
              </nav>
              <div className="app-rail__foot">
                {company ? (
                  <NavLink
                    className={() => `rail-item${activeArea?.id === "company" ? " active" : ""}`}
                    to={company.to}
                    title={t(company.label)}
                    aria-current={activeArea?.id === "company" ? "page" : undefined}
                  >
                    <Icon name={company.icon} className="rail-item__icon" />
                    <span>{t(company.label)}</span>
                  </NavLink>
                ) : null}
                <Popover
                  label={t("shell.account")}
                  trigger={
                    <button type="button" className="rail-account" aria-label={t("shell.account")}>
                      <span className="rail-account__avatar" aria-hidden>
                        {(auth.me?.user.email ?? "?").slice(0, 1).toUpperCase()}
                      </span>
                      <span className="rail-account__text">
                        <span className="rail-account__name">{org?.name ?? "—"}</span>
                        {role ? (
                          <span className="rail-account__role">{t(roleLabel[role])}</span>
                        ) : null}
                      </span>
                    </button>
                  }
                >
                  <div className="account-menu">
                    <p className="account-menu__email">{auth.me?.user.email}</p>
                    <OrgSwitcher />
                    <button
                      type="button"
                      className="account-menu__item"
                      onClick={() => window.dispatchEvent(new Event("dekopen:shortcuts"))}
                    >
                      <Icon name="keyboard" />
                      {t("shell.shortcuts")}
                    </button>
                    <button
                      type="button"
                      className="account-menu__item"
                      onClick={() => void auth.signOut()}
                    >
                      <Icon name="logout" />
                      {t("auth.signOut")}
                    </button>
                  </div>
                </Popover>
                <button
                  type="button"
                  className="rail-collapse"
                  aria-label={collapsed ? "Expandir navegación" : "Contraer navegación"}
                  aria-pressed={collapsed}
                  onClick={() => void look.save({ rail_collapsed: !collapsed })}
                >
                  <Icon name="sidebar" size={20} />
                </button>
              </div>
            </aside>
            <div className="app-body">
              <header className="app-topbar">
                <button
                  type="button"
                  className="rail-toggle"
                  ref={toggleRef}
                  aria-expanded={railOpen}
                  aria-label={t("shell.menu")}
                  onClick={() => setRailOpen((value) => !value)}
                >
                  <Icon name="menu" />
                </button>
                <ShellCrumbs leaf={leaf} />
                <div className="app-topbar__actions">
                  {canUseAssistant && <AiModeBadge />}
                  <button
                    type="button"
                    className="topbar-search"
                    aria-label="Buscar o ejecutar un comando"
                    onClick={() => {
                      window.dispatchEvent(new Event("dekopen:shell-overlay"));
                      setPaletteRequest((value) => value + 1);
                    }}
                  >
                    <Icon name="search" size={16} />
                    <span className="topbar-search__hint">{t("shell.searchHint")}</span>
                    <kbd>{MOD_K_HINT}</kbd>
                  </button>
                  <AttentionBell key={`${org?.id}:${auth.me?.user?.id}:${role}`} />
                  <ShortcutHelp key={org?.id} />
                  {/* INSTALLER has no AI surface — every AI endpoint is gated to
                    the agent callers, so the companion would offer a 403. */}
                  {canUseAssistant ? (
                    <button
                      type="button"
                      className="topbar-assistant"
                      // Narrow screens hide the text; the button keeps its name.
                      aria-label={t("shell.assistant")}
                      onClick={() => setAssistantRequest((value) => value + 1)}
                    >
                      {/* The figure follows the popup's real task, never
                        the route; showing it polls nothing. */}
                      <Companion state={copilotPose} size={28} />
                      <span>{t("shell.assistant")}</span>
                      {copilotStatus.working ? (
                        <span className="topbar-assistant__state">Trabajando</span>
                      ) : null}
                    </button>
                  ) : null}
                </div>
              </header>
              {tabs ? (
                <nav className="area-tabs" aria-label={t(activeArea!.label)}>
                  {tabs.map((section) => (
                    <NavLink key={section.to} to={section.to} end className="area-tabs__item">
                      {t(section.label)}
                    </NavLink>
                  ))}
                </nav>
              ) : null}
              <main className="workspace" id="workspace-main" tabIndex={-1}>
                {children}
              </main>
            </div>
            <CommandPalette
              openRequested={paletteRequest}
              contextKey={`${location.pathname}${location.search}`}
              navItems={paletteItems}
              onNavigate={(to) => navigate(to)}
              organizationId={org?.id ?? null}
            />
            {canUseAssistant && org?.id ? (
              <CopilotWindow
                key={`${org.id}:${auth.me?.user?.id ?? ""}`}
                openRequested={assistantRequest}
                organizationId={org.id}
                userId={auth.me?.user?.id ?? null}
              />
            ) : null}
          </div>
        </CopilotProvider>
      </AssistantSurfaceProvider>
    </ShellLeafContext.Provider>
  );
}
