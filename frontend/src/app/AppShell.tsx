import { type PropsWithChildren, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AiModeBadge } from "../features/assistant/AiModeBadge";
import { NavLink, useLocation, useNavigate } from "react-router-dom";

import { t } from "../i18n/es-CL";
import { BrandMark, Wordmark } from "../brand/Brand";

import { useAuthSession } from "../auth/AuthSessionProvider";
import { MOD_K_HINT } from "../platform";
import { telemetry } from "../telemetry/telemetry";
import { useTheme } from "../theme/ThemeProvider";
import { CommandPalette } from "../features/commands/CommandPalette";
import type { AiJob } from "../api/generated/models/aiJob";
import { AiPresence } from "../features/assistant/AiPresence";
import { AskDekopen } from "../features/assistant/AskDekopen";
import { STATE_LABELS } from "../features/assistant/states";
import { AssistantSurfaceProvider } from "../features/assistant/assistantContext";
import { AttentionBell } from "./AttentionBell";
import { OrgSwitcher } from "./OrgSwitcher";
import { ProjectSwitcher } from "./ProjectSwitcher";
import { RailIcon } from "./railIcons";
import { ShellCrumbs, crumbsFor, useProjectName } from "./ShellCrumbs";
import { ShellLeafContext } from "./shellLeaf";
import { roleLabel } from "./shellUtils";
import { navigationFor } from "./navigation";
import { ShortcutHelp } from "./ShortcutHelp";

export function AppShell({ children }: PropsWithChildren): JSX.Element {
  const auth = useAuthSession();
  const { theme, toggleTheme } = useTheme();
  const location = useLocation();
  const navigate = useNavigate();
  const [leaf, setLeafState] = useState<string | null>(null);
  const setLeaf = useCallback((label: string | null) => setLeafState(label), []);
  const leafContext = useMemo(() => ({ leaf, setLeaf }), [leaf, setLeaf]);
  const [paletteRequest, setPaletteRequest] = useState(0);
  const [assistantRequest, setAssistantRequest] = useState(0);
  const [presenceJob, setPresenceJob] = useState<AiJob | null>(null);
  const onActiveJob = useCallback(
    (job: AiJob | null) =>
      setPresenceJob((previous) =>
        previous?.id === job?.id && previous?.state === job?.state ? previous : job,
      ),
    [],
  );
  const [railOpen, setRailOpen] = useState(false);
  const railRef = useRef<HTMLElement>(null);
  const toggleRef = useRef<HTMLButtonElement>(null);
  const [collapsed, setCollapsed] = useState(() => {
    try {
      return localStorage.getItem("dekopen.rail-collapsed") === "true";
    } catch {
      return false;
    }
  });

  // Close the drawer nav on route change and on Escape — the drawer only
  // exists below the tablet breakpoint; desktop keeps the rail always.
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

  const org = auth.me?.active_organization;
  const role = org?.role;
  const canUseAssistant = role === "OWNER" || role === "ESTIMATOR" || role === "WORKSHOP_MANAGER";
  const parts = location.pathname.split("/").filter(Boolean);
  const projectId = parts[0] === "projects" && parts[1] !== undefined ? parts[1] : null;
  const isStudio = parts[0] === "projects" && parts[2] === "positions" && parts.length >= 4;
  const compact = isStudio || collapsed;
  const domainGroups = navigationFor(role);
  const navItems = domainGroups.flatMap((group) => group.items);
  const projectName = useProjectName(projectId !== "demo" ? projectId : null);

  // Browser tab title tracks the same crumbs the shell renders — tabs and
  // history entries stop all saying "DEKOPEN".
  useEffect(() => {
    const crumbs = crumbsFor(location.pathname, projectName, leaf);
    const head = crumbs
      .slice(-2)
      .map((crumb) => crumb.label)
      .join(" · ");
    document.title = head ? `${head} · DEKOPEN` : "DEKOPEN";
  }, [location.pathname, projectName, leaf]);

  return (
    <ShellLeafContext.Provider value={leafContext}>
      <AssistantSurfaceProvider>
        <div
          className={`app-shell${railOpen ? " rail-open" : ""}${compact ? " rail-collapsed" : ""}`}
          data-studio={isStudio || undefined}
          data-density={role === "OPERATOR" || role === "INSTALLER" ? "workshop" : "office"}
          data-theme={theme}
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
            <div className="app-rail__brand">
              <span className="rail-brand-full">
                <Wordmark width={120} />
              </span>
              <span className="rail-brand-compact">
                <BrandMark size={24} title="DEKOPEN" />
              </span>
            </div>
            <nav className="app-rail__nav" aria-label={t("shell.navigation")}>
              {domainGroups.map((group) => (
                <div key={group.id} className="rail-group">
                  {group.title && <p className="rail-group__title">{t(group.title)}</p>}
                  {group.items.map((item) => (
                    <NavLink
                      className="rail-item"
                      key={item.to}
                      to={item.to}
                      title={t(item.label)}
                      aria-label={t(item.label)}
                    >
                      <RailIcon to={item.to} />
                      <span>{t(item.label)}</span>
                    </NavLink>
                  ))}
                </div>
              ))}
            </nav>
            <button
              type="button"
              className="rail-collapse"
              aria-label={collapsed ? "Expandir navegación" : "Contraer navegación"}
              aria-pressed={collapsed}
              onClick={() =>
                setCollapsed((value) => {
                  try {
                    localStorage.setItem("dekopen.rail-collapsed", String(!value));
                  } catch {
                    /* Session preference remains usable. */
                  }
                  return !value;
                })
              }
            >
              <svg
                aria-hidden="true"
                viewBox="0 0 24 24"
                width="16"
                height="16"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.5"
              >
                <path d={collapsed ? "m9 6 6 6-6 6" : "m15 6-6 6 6 6"} />
              </svg>
              <span>{collapsed ? "Expandir" : "Contraer"}</span>
            </button>
            <div className="app-rail__user">
              <div className="app-rail__identity">
                <span className="app-rail__email" title={auth.me?.user.email ?? undefined}>
                  {auth.me?.user.email ? auth.me.user.email.split("@")[0] : "—"}
                </span>
                {role && <span className="app-rail__role">{t(roleLabel[role])}</span>}
              </div>
              <div className="app-rail__user-actions">
                <button
                  type="button"
                  className="rail-icon-button"
                  onClick={toggleTheme}
                  aria-label={t("theme.toggle")}
                  title={t(theme === "light" ? "theme.toDark" : "theme.toLight")}
                >
                  <svg
                    aria-hidden="true"
                    width="20"
                    height="20"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.5"
                  >
                    {theme === "light" ? (
                      <path d="M19 15a8 8 0 0 1-10-10A8 8 0 1 0 19 15Z" />
                    ) : (
                      <>
                        <circle cx="12" cy="12" r="4" />
                        <path d="M12 2v3M12 19v3M2 12h3M19 12h3M5 5l2 2M17 17l2 2M19 5l-2 2M7 17l-2 2" />
                      </>
                    )}
                  </svg>
                </button>
                <button
                  type="button"
                  className="rail-icon-button"
                  onClick={() => void auth.signOut()}
                  aria-label={t("auth.signOut")}
                  title={t("auth.signOut")}
                >
                  <svg
                    aria-hidden="true"
                    width="20"
                    height="20"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.5"
                  >
                    <path d="M10 3H4v18h6M8 12h12m-5-5 5 5-5 5" />
                  </svg>
                </button>
              </div>
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
                <svg
                  aria-hidden="true"
                  width="20"
                  height="20"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.5"
                >
                  <path d="M3 6h18M3 12h18M3 18h18" />
                </svg>
              </button>
              <ShellCrumbs leaf={leaf} />
              <div className="app-topbar__actions">
                <OrgSwitcher />
                <ProjectSwitcher />
                {canUseAssistant && <AiModeBadge />}
                <button
                  type="button"
                  className="topbar-search"
                  aria-label="Buscar o ejecutar un comando"
                  title="Buscar o ejecutar · Ctrl K"
                  onClick={() => {
                    window.dispatchEvent(new Event("dekopen:shell-overlay"));
                    setPaletteRequest((value) => value + 1);
                  }}
                >
                  <svg width="13" height="13" viewBox="0 0 13 13" fill="none" aria-hidden>
                    <circle cx="5.6" cy="5.6" r="4.1" stroke="currentColor" strokeWidth="1.3" />
                    <path
                      d="m8.7 8.7 2.8 2.8"
                      stroke="currentColor"
                      strokeWidth="1.3"
                      strokeLinecap="round"
                    />
                  </svg>
                  <span>{t("shell.searchHint")}</span>
                  <kbd>{MOD_K_HINT}</kbd>
                  <kbd>/</kbd>
                </button>
                <AttentionBell key={`${org?.id}:${auth.me?.user.id}:${role}`} />
                <ShortcutHelp key={org?.id} />
                {/* INSTALLER has no AI surface — every ai endpoint is gated to
                    _AGENT_CALLERS, so the orb would offer a 403 wall. */}
                {canUseAssistant ? (
                  <>
                    {/* The orb always opens the dock — a pressing job gets its
                        own chip so an unlucky FAILED_RETRYABLE can never make
                        the dock unreachable (AI review P1-1). */}
                    <button
                      type="button"
                      className="topbar-button topbar-ai"
                      aria-label={t("shell.aiEntry")}
                      title={t("shell.aiEntry")}
                      onClick={() => setAssistantRequest((value) => value + 1)}
                    >
                      <AiPresence
                        userId={auth.me?.user.id ?? null}
                        organizationId={org?.id ?? null}
                        size={22}
                        onActiveJob={onActiveJob}
                      />
                      <span className="topbar-ai-label">{t("shell.aiEntry")}</span>
                    </button>
                    {presenceJob ? (
                      <button
                        type="button"
                        className="topbar-button topbar-ai-job"
                        data-state={presenceJob?.state.toLowerCase()}
                        title={t("aiws.presenceOpen")}
                        onClick={() => navigate(`/assistant?job=${presenceJob.id}`)}
                      >
                        {t(STATE_LABELS[presenceJob.state] ?? "aiws.jobs")}
                      </button>
                    ) : null}
                  </>
                ) : null}
              </div>
            </header>
            <main className="workspace" id="workspace-main" tabIndex={-1}>
              {children}
            </main>
          </div>
          <CommandPalette
            openRequested={paletteRequest}
            contextKey={`${location.pathname}${location.search}`}
            navItems={navItems.map((item) => ({ to: item.to, label: t(item.label) }))}
            onNavigate={(to) => navigate(to)}
            organizationId={org?.id ?? null}
          />
          {canUseAssistant ? (
            <AskDekopen
              openRequested={assistantRequest}
              hideTrigger
              organizationId={org?.id ?? null}
              userId={auth.me?.user.id ?? null}
            />
          ) : null}
        </div>
      </AssistantSurfaceProvider>
    </ShellLeafContext.Provider>
  );
}
