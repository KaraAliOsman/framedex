import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useMatch, useSearchParams } from "react-router-dom";

import type { PositionResponse, ProjectResponse } from "../../api/generated/models";
import { isWorkView, readWorkView, saveWorkView, type WorkView } from "../../app/workPreferences";

/** Interface state of one work for one person (v1 final 02).
 *
 * Identity `userId:orgId:projectId`. It owns presentation only — the work,
 * its positions and revision stay in the shared server query
 * (`useProjectView`). Mesa de obra and Estudio read the same work; switching
 * view never saves, recalculates or duplicates anything.
 *
 * Separate concepts, never one interchangeable array:
 * - `view`: Mesa or Estudio (query → per user/org preference → Mesa);
 * - `activeId`: the position whose drawing is shown;
 * - `sessionId`: the position held by the one editing session (it survives
 *   Mesa ↔ Estudio ↔ wide editor and only changes by deliberate navigation);
 * - batch checkboxes, filters and canvas selection live in their components.
 */

export type EditorRoute = { kind: "edit"; positionId: string } | { kind: "new" } | null;

export type EditorPresentation = "studio" | "expanded" | "hidden";

export function useEditorRoute(): EditorRoute {
  const edit = useMatch("/projects/:id/positions/:posId/edit");
  const fresh = useMatch("/projects/:id/positions/new");
  if (edit?.params.posId) return { kind: "edit", positionId: edit.params.posId };
  if (fresh) return { kind: "new" };
  return null;
}

/** First real position by the work's order — never an invented id. */
export function firstPosition(
  project: ProjectResponse | null | undefined,
): PositionResponse | null {
  const positions = [...(project?.positions ?? [])];
  positions.sort(
    (a, b) =>
      (a.display_order ?? a.position_index) - (b.display_order ?? b.position_index) ||
      a.position_index - b.position_index,
  );
  return positions[0] ?? null;
}

export function useProjectWorkspaceState({
  userId,
  orgId,
  project,
  section,
  unified = false,
}: {
  userId: string;
  orgId: string;
  project: ProjectResponse | null;
  /** null = Ventanas; other destinations show the same panels in both views. */
  section: string | null;
  /** DEKOPEN 2: one visible editing session, with the legacy views behind a flag. */
  unified?: boolean;
}): {
  view: WorkView;
  setView(view: WorkView): void;
  activeId: string | null;
  setActiveId(id: string | null): void;
  editorRoute: EditorRoute;
  presentation: EditorPresentation;
  /** Position held by the editing session ("new" while creating). */
  sessionId: string | null;
  /** Internal, validated return path to the work (never an arbitrary URL). */
  workPath(options?: {
    view?: WorkView;
    position?: string | null;
    section?: string | null;
  }): string;
} {
  const [params, setParams] = useSearchParams();
  const editorRoute = useEditorRoute();
  const projectId = project?.id ?? null;
  const positions = project?.positions;

  const queried = params.get("view");
  const view: WorkView = isWorkView(queried) ? queried : readWorkView(userId, orgId);

  // Active position: valid query → last valid selection of this work → first
  // real position. An id from another work or a deleted one is normalized.
  const lastValid = useRef<string | null>(null);
  const requested = params.get("position");
  const valid = (id: string | null | undefined): id is string =>
    !!id && !!positions?.some((position) => position.id === id);
  const activeId = valid(requested)
    ? requested
    : valid(lastValid.current)
      ? lastValid.current
      : (firstPosition(project)?.id ?? null);
  useEffect(() => {
    if (activeId) lastValid.current = activeId;
  }, [activeId]);

  // Normalize an invalid ?position= without adding a history entry.
  useEffect(() => {
    if (!positions || !requested || valid(requested)) return;
    setParams(
      (current) => {
        const next = new URLSearchParams(current);
        if (activeId) next.set("position", activeId);
        else next.delete("position");
        return next;
      },
      { replace: true },
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [positions, requested, activeId]);

  const setView = useCallback(
    (next: WorkView) => {
      saveWorkView(userId, orgId, next);
      // A presentation change replaces the entry: Back is not filled with
      // cosmetic switches.
      setParams(
        (current) => {
          const value = new URLSearchParams(current);
          value.set("view", next);
          return value;
        },
        { replace: true },
      );
    },
    [userId, orgId, setParams],
  );

  const setActiveId = useCallback(
    (id: string | null) => {
      setParams(
        (current) => {
          const value = new URLSearchParams(current);
          if (id) value.set("position", id);
          else value.delete("position");
          return value;
        },
        { replace: true },
      );
    },
    [setParams],
  );

  const presentation: EditorPresentation = unified
    ? section === null
      ? "studio"
      : "hidden"
    : editorRoute
      ? "expanded"
      : view === "estudio" && section === null
        ? "studio"
        : "hidden";

  // The editing session follows deliberate entries (wide editor or Estudio)
  // and is kept while visiting Mesa or another destination of the same work.
  const [sessionId, setSessionId] = useState<string | null>(null);
  const wanted =
    editorRoute?.kind === "edit"
      ? editorRoute.positionId
      : editorRoute?.kind === "new"
        ? "new"
        : presentation === "studio"
          ? activeId
          : null;
  useEffect(() => {
    if (wanted && wanted !== sessionId) setSessionId(wanted);
  }, [wanted, sessionId]);
  // A session on a position deleted by an operation is closed.
  useEffect(() => {
    if (sessionId && sessionId !== "new" && positions && !valid(sessionId)) setSessionId(null);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [positions, sessionId]);

  const workPath = useCallback(
    (options: { view?: WorkView; position?: string | null; section?: string | null } = {}) => {
      if (!projectId) return "/projects";
      const value = new URLSearchParams();
      value.set("view", options.view ?? view);
      const position = options.position === undefined ? activeId : options.position;
      if (position && valid(position)) value.set("position", position);
      const target = options.section === undefined ? section : options.section;
      if (target) value.set("section", target);
      return `/projects/${projectId}?${value.toString()}`;
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [projectId, view, activeId, section, positions],
  );

  return useMemo(
    () => ({
      view,
      setView,
      activeId,
      setActiveId,
      editorRoute,
      presentation,
      sessionId: wanted ?? sessionId,
      workPath,
    }),
    [view, setView, activeId, setActiveId, editorRoute, presentation, wanted, sessionId, workPath],
  );
}
