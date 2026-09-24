import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type PropsWithChildren,
} from "react";
import { matchPath, useLocation } from "react-router-dom";

/** The contextual assistant's (surface, refs) — derived from the route by
 * default; a page can override it (e.g. ProductionPage while a work order is
 * selected). Refs are identifiers only — the server builds the real context. */
export interface AssistantContextValue {
  surface: string;
  refs: Record<string, string>;
}

const AssistantSurface = createContext<{
  value: AssistantContextValue;
  setOverride: (value: AssistantContextValue | null) => void;
} | null>(null);

const SURFACE_ROUTES: {
  pattern: string;
  surface: string;
  refs: (params: Record<string, string | undefined>) => Record<string, string>;
}[] = [
  {
    pattern: "/projects/:id/positions/:posId/edit",
    surface: "position",
    refs: (p) => ({ project_id: p.id ?? "", position_id: p.posId ?? "" }),
  },
  {
    pattern: "/projects/:id/pricing",
    surface: "quotation",
    refs: (p) => ({ project_id: p.id ?? "" }),
  },
  {
    pattern: "/projects/:id/*",
    surface: "project",
    refs: (p) => ({ project_id: p.id ?? "" }),
  },
  { pattern: "/projects", surface: "projects", refs: () => ({}) },
  { pattern: "/production", surface: "production", refs: () => ({}) },
  { pattern: "/purchasing", surface: "purchasing", refs: () => ({}) },
  { pattern: "/catalogs/*", surface: "catalog", refs: () => ({}) },
  { pattern: "/clients", surface: "clients", refs: () => ({}) },
  { pattern: "/settings/*", surface: "settings", refs: () => ({}) },
  // Org-level commercial config surfaces answer through the organization
  // projection — no dedicated pricing surface exists server-side.
  { pattern: "/pricing/*", surface: "settings", refs: () => ({}) },
  { pattern: "/dashboard", surface: "dashboard", refs: () => ({}) },
  { pattern: "/", surface: "dashboard", refs: () => ({}) },
];

export function routeContext(pathname: string): AssistantContextValue {
  for (const route of SURFACE_ROUTES) {
    const match = matchPath({ path: route.pattern, end: true }, pathname);
    if (match) {
      return { surface: route.surface, refs: route.refs(match.params) };
    }
  }
  return { surface: "dashboard", refs: {} };
}

export function AssistantSurfaceProvider({ children }: PropsWithChildren): JSX.Element {
  const location = useLocation();
  const [override, setOverride] = useState<AssistantContextValue | null>(null);
  const value = useMemo(() => {
    const derived = override ?? routeContext(location.pathname);
    return { value: derived, setOverride };
  }, [location.pathname, override]);
  return <AssistantSurface.Provider value={value}>{children}</AssistantSurface.Provider>;
}

/** The live assistant context for the current route (or a page override). */
export function useAssistantContext(): AssistantContextValue {
  const ctx = useContext(AssistantSurface);
  // useMemo: the fallback literal must keep a stable identity across renders —
  // consumers key effects on the serialized refs.
  return useMemo(() => ctx?.value ?? { surface: "dashboard", refs: {} }, [ctx?.value]);
}

/** A page declares a more specific assistant context while mounted (e.g. the
 * selected work order). Pass null to restore the route-derived value. The
 * effect keys on the serialized refs so an inline object can't loop the
 * override. */
export function useAssistantSurface(surface: string | null, refs?: Record<string, string>): void {
  const ctx = useContext(AssistantSurface);
  const setOverride = ctx?.setOverride;
  const refsKey = refs ? JSON.stringify(refs) : "";
  useEffect(() => {
    if (!setOverride || !surface) return;
    setOverride({ surface, refs: refs ? (JSON.parse(refsKey) as Record<string, string>) : {} });
    return () => setOverride(null);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- refsKey is the
    // stable serialization of refs; the raw object would re-fire per render.
  }, [setOverride, surface, refsKey]);
}
