import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type PointerEvent as ReactPointerEvent,
} from "react";

import { useQueryClient } from "@tanstack/react-query";
import { aiThreadUpdate, aiThreadsCreate, aiThreadsList } from "../../api/generated/dekopen";
import type { AiThread } from "../../api/generated/models/aiThread";
import {
  readPopupGeometry,
  savePopupGeometry,
  type PopupGeometry,
} from "../../app/workPreferences";
import { ValidatedForm } from "../../ui/FormValidation";
import { Icon } from "../../ui/Icon";
import { AgentBody } from "./AgentBody";
import { useAssistantContext } from "./assistantContext";
import { COPILOT_DELEGATE_EVENT, type CopilotDelegation } from "./copilotBridge";
import {
  AUTONOMY_OPTIONS,
  clearOtherSessions,
  readAutonomy,
  readMode,
  readSession,
  saveAutonomy,
  saveMode,
  saveSession,
  type AutonomyPolicy,
  type InteractionMode,
} from "./copilotPrefs";
import { publishCopilotStatus } from "./copilotStatus";
import { Companion, companionStateFor, type CompanionState } from "./Companion";
import { SURFACE_LABELS } from "./surfaces";
import { projectKey, type ProjectView } from "../projects/useProject";
import "./assistant.css";
import "./copilot.css";

/** The optional global copilot (dirección final 05 · 1).
 *
 * One non-modal popup per shell: no scrim, no focus trap, no change to the
 * page's columns, inspector or margins. 420 × 600 by default, at least
 * 340 × 420, always inside the viewport; dragged by its header, resized by
 * its edges, adjustable from the keyboard. Minimizing or closing keeps the
 * conversation, the draft and any running job — stopping work is a
 * separate, named action. Only geometry and preferences are stored. */

const MIN_W = 340;
const MIN_H = 420;
const DEFAULT_W = 420;
const DEFAULT_H = 600;
const GAP = 16;
const MOBILE = 768;

type Edge = "n" | "s" | "e" | "w" | "ne" | "nw" | "se" | "sw";
const EDGES: Edge[] = ["n", "s", "e", "w", "ne", "nw", "se", "sw"];

function viewport(): { width: number; height: number } {
  return { width: window.innerWidth, height: window.innerHeight };
}

export function clampGeometry(geometry: PopupGeometry, view = viewport()): PopupGeometry {
  const maxW = Math.max(MIN_W, view.width - GAP * 2);
  const maxH = Math.max(MIN_H, view.height - GAP * 2);
  const width = Math.min(Math.max(geometry.width, Math.min(MIN_W, maxW)), maxW);
  const height = Math.min(Math.max(geometry.height, Math.min(MIN_H, maxH)), maxH);
  const x = Math.min(Math.max(geometry.x, GAP), Math.max(GAP, view.width - width - GAP));
  const y = Math.min(Math.max(geometry.y, GAP), Math.max(GAP, view.height - height - GAP));
  return { x, y, width, height };
}

function defaultGeometry(): PopupGeometry {
  const view = viewport();
  return clampGeometry({
    width: DEFAULT_W,
    height: DEFAULT_H,
    x: view.width - DEFAULT_W - GAP * 2,
    y: view.height - DEFAULT_H - GAP * 2,
  });
}

function relativeDay(value: string): string {
  const date = new Date(value);
  const today = new Date();
  const days = Math.round(
    (today.setHours(0, 0, 0, 0) - new Date(date).setHours(0, 0, 0, 0)) / 86_400_000,
  );
  if (days <= 0) return date.toLocaleTimeString("es-CL", { hour: "2-digit", minute: "2-digit" });
  if (days === 1) return "Ayer";
  return date.toLocaleDateString("es-CL", { day: "numeric", month: "short" });
}

export function CopilotWindow({
  organizationId,
  userId,
  openRequested = 0,
}: {
  organizationId: string;
  userId: string | null;
  /** Incremental open signal from the shell's «Asistente» button. */
  openRequested?: number;
}): JSX.Element | null {
  const headers = useMemo(
    () => ({ headers: { "X-Organization-ID": organizationId } }),
    [organizationId],
  );
  const initial = useMemo(() => readSession(userId, organizationId), [userId, organizationId]);
  const [open, setOpen] = useState(initial.open);
  // Mounted on first open only (opening reads history, never the model);
  // afterwards closing or minimizing hides it so the draft, the thread and
  // any running job survive.
  const [mounted, setMounted] = useState(initial.open);
  const [minimized, setMinimized] = useState(initial.minimized);
  const [threadId, setThreadId] = useState<string | null>(initial.threadId);
  const [mode, setModeState] = useState<InteractionMode>(() => readMode(userId, organizationId));
  const [autonomy, setAutonomyState] = useState<AutonomyPolicy>(() =>
    readAutonomy(userId, organizationId),
  );
  const [geometry, setGeometry] = useState<PopupGeometry>(() =>
    clampGeometry(readPopupGeometry(userId, organizationId) ?? defaultGeometry()),
  );
  const [maximized, setMaximized] = useState(false);
  const [mobile, setMobile] = useState(() => viewport().width < MOBILE);
  const [history, setHistory] = useState(false);
  const [adjusting, setAdjusting] = useState<PopupGeometry | null>(null);
  const [prefill, setPrefill] = useState<{ text: string; nonce: number } | null>(null);
  const [delegatedRefs, setDelegatedRefs] = useState<Record<string, string> | null>(null);
  const [contextCleared, setContextCleared] = useState(false);
  const [jobState, setJobState] = useState<string | null>(null);
  const [composing, setComposing] = useState(false);
  const panel = useRef<HTMLElement>(null);
  const invoker = useRef<HTMLElement | null>(null);
  const live = useRef<PopupGeometry>(geometry);
  live.current = geometry;

  const { surface, refs } = useAssistantContext();

  // Identity: another person or organization never inherits this tab's
  // popup state; the shell re-keys this component on identity change.
  useEffect(() => {
    clearOtherSessions(userId, organizationId);
  }, [userId, organizationId]);

  useEffect(() => {
    saveSession(userId, organizationId, { open, minimized, threadId });
  }, [open, minimized, threadId, userId, organizationId]);

  const show = useCallback(() => {
    if (
      document.activeElement instanceof HTMLElement &&
      !panel.current?.contains(document.activeElement)
    )
      invoker.current = document.activeElement;
    setOpen(true);
    setMounted(true);
    setMinimized(false);
  }, []);

  useEffect(() => {
    if (openRequested > 0) show();
  }, [openRequested, show]);

  // A delegation from a manual surface opens the same popup with an explicit
  // context and a prefilled request. It never sends by itself.
  useEffect(() => {
    const onDelegate = (event: Event) => {
      const detail = (event as CustomEvent<CopilotDelegation>).detail;
      if (!detail) return;
      show();
      setModeState(detail.mode);
      saveMode(userId, organizationId, detail.mode);
      const sealed: Record<string, string> = {};
      for (const [key, value] of Object.entries(detail.refs ?? {})) {
        if (typeof value === "string") sealed[key] = value;
        else if (Array.isArray(value)) sealed[key] = value.join(",");
      }
      setDelegatedRefs(Object.keys(sealed).length ? sealed : null);
      setContextCleared(false);
      setPrefill({ text: detail.text, nonce: Date.now() });
    };
    window.addEventListener(COPILOT_DELEGATE_EVENT, onDelegate);
    return () => window.removeEventListener(COPILOT_DELEGATE_EVENT, onDelegate);
  }, [show, userId, organizationId]);

  // Keep the window recoverable on resize/zoom/orientation changes.
  useEffect(() => {
    const onResize = () => {
      setMobile(viewport().width < MOBILE);
      setGeometry((previous) => clampGeometry(previous));
    };
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  // The read context follows the route; clearing it lasts until it changes.
  const contextKey = `${surface}:${JSON.stringify(refs)}`;
  useEffect(() => {
    setContextCleared(false);
    setDelegatedRefs(null);
  }, [contextKey]);
  const readSurface = contextCleared ? "dashboard" : surface;
  const readRefs = contextCleared ? {} : { ...refs, ...(delegatedRefs ?? {}) };
  // Name the destination the way the person sees it: «V1 · Colegio» rather
  // than a surface code, so it is obvious which work a request will change.
  const queryClient = useQueryClient();
  const openWork = readRefs.project_id
    ? queryClient.getQueryData<ProjectView>(projectKey(organizationId, readRefs.project_id))
        ?.project
    : undefined;
  const openWindow = readRefs.position_id
    ? openWork?.positions?.find((item) => item.id === readRefs.position_id)
    : undefined;
  const windowName = openWindow
    ? openWindow.location_tag || `Ventana ${openWindow.position_index}`
    : null;
  const workName = openWork ? openWork.name || openWork.code : null;
  const contextLabel = contextCleared
    ? null
    : `${
        windowName && workName
          ? `${windowName} · ${workName}`
          : workName
            ? `obra ${workName}`
            : `${SURFACE_LABELS[surface] ?? "tu trabajo actual"}${readRefs.position_id && surface !== "position" ? " · ventana abierta" : ""}`
      }${readRefs.selection ? " · selección" : ""}`;

  const pose: CompanionState =
    composing && (!jobState || ["SUCCEEDED", "CANCELED"].includes(jobState))
      ? "input"
      : companionStateFor(jobState ?? undefined);
  useEffect(() => {
    publishCopilotStatus({
      state: pose,
      working: jobState !== null && ["QUEUED", "PLANNING", "RUNNING"].includes(jobState),
    });
  }, [pose, jobState]);

  function setMode(next: InteractionMode): void {
    setModeState(next);
    saveMode(userId, organizationId, next);
  }

  function setAutonomy(next: AutonomyPolicy): void {
    // A preference change governs new tasks only; each job keeps its seal.
    setAutonomyState(next);
    saveAutonomy(userId, organizationId, next);
  }

  function hide(): void {
    setOpen(false);
    setHistory(false);
    setAdjusting(null);
    const target = invoker.current;
    if (target && document.contains(target)) target.focus();
  }

  function commit(next: PopupGeometry): void {
    const clamped = clampGeometry(next);
    setGeometry(clamped);
    savePopupGeometry(userId, organizationId, clamped);
  }

  // Pointer drag (header) and resize (edges): 1:1 with pointer capture, the
  // element follows directly and React commits once on release.
  function startPointer(event: ReactPointerEvent<HTMLElement>, edge: Edge | "move"): void {
    if (mobile || maximized || event.button !== 0) return;
    if (
      edge === "move" &&
      (event.target as HTMLElement).closest("button, input, select, [role='radio']")
    )
      return;
    event.preventDefault();
    const element = panel.current;
    if (!element) return;
    const origin = { x: event.clientX, y: event.clientY };
    const start = { ...live.current };
    const target = event.currentTarget;
    target.setPointerCapture(event.pointerId);
    let next = start;
    const move = (moveEvent: PointerEvent) => {
      const dx = moveEvent.clientX - origin.x;
      const dy = moveEvent.clientY - origin.y;
      if (edge === "move") next = { ...start, x: start.x + dx, y: start.y + dy };
      else {
        next = { ...start };
        if (edge.includes("e")) next.width = start.width + dx;
        if (edge.includes("s")) next.height = start.height + dy;
        if (edge.includes("w")) {
          next.width = Math.max(MIN_W, start.width - dx);
          next.x = start.x + (start.width - next.width);
        }
        if (edge.includes("n")) {
          next.height = Math.max(MIN_H, start.height - dy);
          next.y = start.y + (start.height - next.height);
        }
      }
      next = clampGeometry(next);
      element.style.left = `${next.x}px`;
      element.style.top = `${next.y}px`;
      element.style.width = `${next.width}px`;
      element.style.height = `${next.height}px`;
    };
    const end = () => {
      target.removeEventListener("pointermove", move);
      target.removeEventListener("pointerup", end);
      target.removeEventListener("pointercancel", end);
      commit(next);
    };
    target.addEventListener("pointermove", move);
    target.addEventListener("pointerup", end);
    target.addEventListener("pointercancel", end);
  }

  function onKeyDown(event: React.KeyboardEvent<HTMLElement>): void {
    if (event.nativeEvent.isComposing) return;
    if (adjusting) {
      const step = 16;
      const next = { ...adjusting };
      if (event.key === "Enter") {
        event.preventDefault();
        commit(adjusting);
        setAdjusting(null);
        return;
      }
      if (event.key === "Escape") {
        event.preventDefault();
        setAdjusting(null);
        return;
      }
      const resize = event.shiftKey;
      if (event.key === "ArrowLeft") resize ? (next.width -= step) : (next.x -= step);
      else if (event.key === "ArrowRight") resize ? (next.width += step) : (next.x += step);
      else if (event.key === "ArrowUp") resize ? (next.height -= step) : (next.y -= step);
      else if (event.key === "ArrowDown") resize ? (next.height += step) : (next.y += step);
      else return;
      event.preventDefault();
      setAdjusting(clampGeometry(next));
      return;
    }
    if (event.key === "Escape" && !event.defaultPrevented) {
      if (history) {
        setHistory(false);
        return;
      }
      if ((event.target as HTMLElement).closest("details[open], [role='menu']")) return;
      hide();
    }
  }

  if (!mounted) return null;

  const shown = adjusting ?? geometry;
  const style =
    mobile || maximized
      ? undefined
      : { left: shown.x, top: shown.y, width: shown.width, height: shown.height };

  const mini =
    open && minimized ? (
      <div className="copilot-mini" role="region" aria-label="Asistente minimizado">
        <button
          type="button"
          className="copilot-mini__restore"
          onClick={() => setMinimized(false)}
          aria-label="Restaurar el asistente"
        >
          <Companion state={pose} size={28} />
          <span>Asistente</span>
          {jobState && ["QUEUED", "PLANNING", "RUNNING"].includes(jobState) ? (
            <span className="copilot-mini__state">Trabajando</span>
          ) : null}
        </button>
        <button
          type="button"
          className="ui-icon-button copilot__icon"
          onClick={hide}
          aria-label="Cerrar el asistente"
        >
          <Icon name="close" size={16} />
        </button>
      </div>
    ) : null;

  return (
    <>
      {mini}
      <section
        ref={panel}
        className={`copilot${maximized ? " is-maximized" : ""}${mobile ? " is-mobile" : ""}${
          adjusting ? " is-adjusting" : ""
        }`}
        style={style}
        role="dialog"
        aria-modal="false"
        aria-labelledby="copilot-title"
        hidden={!open || minimized}
        tabIndex={-1}
        onKeyDown={onKeyDown}
      >
        <header className="copilot__header" onPointerDown={(event) => startPointer(event, "move")}>
          <Companion state={pose} size={24} />
          <h2 id="copilot-title" className="copilot__title">
            Asistente
          </h2>
          <div className="copilot__modes" role="radiogroup" aria-label="Modo del asistente">
            {(["chat", "work"] as const).map((value) => (
              <button
                key={value}
                type="button"
                role="radio"
                aria-checked={mode === value}
                className="copilot__mode"
                onClick={() => setMode(value)}
              >
                {value === "chat" ? "Preguntar" : "Encargar"}
              </button>
            ))}
          </div>
          <div className="copilot__tools">
            <button
              type="button"
              className="ui-icon-button copilot__icon"
              aria-label="Historial de conversaciones"
              aria-pressed={history}
              onClick={() => setHistory((value) => !value)}
            >
              <Icon name="clock" size={16} />
            </button>
            {!mobile ? (
              <button
                type="button"
                className="ui-icon-button copilot__icon"
                aria-label="Mover o cambiar tamaño con el teclado"
                onClick={() => {
                  setAdjusting(geometry);
                  panel.current?.focus();
                }}
              >
                <Icon name="dimension" size={16} />
              </button>
            ) : null}
            <button
              type="button"
              className="ui-icon-button copilot__icon"
              aria-label="Minimizar el asistente"
              onClick={() => setMinimized(true)}
            >
              <Icon name="chevronDown" size={16} />
            </button>
            {!mobile ? (
              <button
                type="button"
                className="ui-icon-button copilot__icon"
                aria-label={maximized ? "Restaurar tamaño" : "Ampliar el asistente"}
                aria-pressed={maximized}
                onClick={() => setMaximized((value) => !value)}
              >
                <Icon name={maximized ? "restore" : "maximize"} size={16} />
              </button>
            ) : null}
            <button
              type="button"
              className="ui-icon-button copilot__icon"
              aria-label={mobile ? "Volver al trabajo" : "Cerrar el asistente"}
              onClick={hide}
            >
              <Icon name="close" size={16} />
            </button>
          </div>
        </header>
        {adjusting ? (
          <p className="copilot__adjust" role="status">
            Flechas: mover · Mayús + flechas: tamaño · Enter: guardar · Esc: salir
          </p>
        ) : null}
        {mode === "work" ? (
          <div className="copilot__policy" role="radiogroup" aria-label="Autonomía del trabajo">
            {AUTONOMY_OPTIONS.map((option) => (
              <button
                key={option.value}
                type="button"
                role="radio"
                aria-checked={autonomy === option.value}
                title={option.hint}
                className="copilot__policy-option"
                onClick={() => setAutonomy(option.value)}
              >
                {option.label}
              </button>
            ))}
          </div>
        ) : null}
        <div className="copilot__main">
          {history ? (
            <ThreadHistory
              headers={headers}
              current={threadId}
              onOpen={(id) => {
                setThreadId(id);
                if (!maximized) setHistory(false);
              }}
              onNew={async () => {
                // «Nuevo» opens another conversation; the previous one stays.
                try {
                  const created = await aiThreadsCreate(
                    { interaction_mode: mode, autonomy },
                    headers,
                  );
                  setThreadId(created.status === 201 ? created.data.id : null);
                } catch {
                  setThreadId(null);
                }
                if (!maximized) setHistory(false);
              }}
            />
          ) : null}
          <div className="copilot__body" hidden={history && !maximized}>
            <AgentBody
              key={organizationId}
              organizationId={organizationId}
              userId={userId}
              surface={readSurface}
              refs={readRefs}
              threadId={threadId}
              onThread={setThreadId}
              interactionMode={mode}
              autonomy={autonomy}
              onInteractionMode={setMode}
              prefill={prefill}
              contextLabel={contextLabel}
              onClearContext={() => setContextCleared(true)}
              onJobState={setJobState}
              onComposing={setComposing}
            />
          </div>
        </div>
        {!mobile && !maximized
          ? EDGES.map((edge) => (
              <span
                key={edge}
                className={`copilot__edge copilot__edge--${edge}`}
                aria-hidden="true"
                onPointerDown={(event) => startPointer(event, edge)}
              />
            ))
          : null}
      </section>
    </>
  );
}

function ThreadHistory({
  headers,
  current,
  onOpen,
  onNew,
}: {
  headers: { headers: Record<string, string> };
  current: string | null;
  onOpen: (id: string) => void;
  onNew: () => void | Promise<void>;
}): JSX.Element {
  const [query, setQuery] = useState("");
  const [archived, setArchived] = useState(false);
  const [items, setItems] = useState<AiThread[]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [state, setState] = useState<"loading" | "ready" | "error">("loading");
  const [renaming, setRenaming] = useState<string | null>(null);
  const [draft, setDraft] = useState("");

  const load = useCallback(
    async (more: string | null) => {
      setState("loading");
      try {
        const response = await aiThreadsList(
          { q: query || undefined, archived, ...(more ? { cursor: more } : {}) },
          headers,
        );
        if (response.status !== 200) throw new Error("threads");
        setItems((previous) =>
          more ? [...previous, ...response.data.items] : response.data.items,
        );
        setCursor(response.data.next_cursor);
        setState("ready");
      } catch {
        setState("error");
      }
    },
    [query, archived, headers],
  );

  useEffect(() => {
    const timer = window.setTimeout(() => void load(null), query ? 250 : 0);
    return () => window.clearTimeout(timer);
  }, [load, query]);

  async function update(id: string, patch: { title?: string; archived?: boolean }): Promise<void> {
    try {
      const response = await aiThreadUpdate(id, patch, headers);
      if (response.status !== 200) throw new Error("update");
      if (patch.archived !== undefined)
        setItems((previous) => previous.filter((item) => item.id !== id));
      else setItems((previous) => previous.map((item) => (item.id === id ? response.data : item)));
    } catch {
      setState("error");
    }
  }

  return (
    <nav className="copilot-history" aria-label="Historial de conversaciones">
      <div className="copilot-history__bar">
        <input
          type="search"
          className="ui-input"
          placeholder="Buscar conversación"
          aria-label="Buscar conversación"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
        />
        <button
          type="button"
          className="ui-button ui-button--primary ui-button--compact"
          onClick={() => void onNew()}
        >
          <Icon name="plus" size={16} />
          Nueva
        </button>
      </div>
      <label className="copilot-history__toggle">
        <input
          type="checkbox"
          checked={archived}
          onChange={(event) => setArchived(event.target.checked)}
        />
        Ver archivadas
      </label>
      {state === "error" ? (
        <p className="copilot-history__empty">No pudimos cargar el historial.</p>
      ) : null}
      {state !== "error" && !items.length && state === "ready" ? (
        <p className="copilot-history__empty">
          {archived ? "No hay conversaciones archivadas." : "Todavía no hay conversaciones."}
        </p>
      ) : null}
      <ul className="copilot-history__list">
        {items.map((item) => (
          <li key={item.id} aria-current={item.id === current ? "true" : undefined}>
            {renaming === item.id ? (
              <ValidatedForm
                className="copilot-history__rename"
                onSubmit={(event) => {
                  event.preventDefault();
                  if (draft.trim()) void update(item.id, { title: draft.trim() });
                  setRenaming(null);
                }}
              >
                <input
                  className="ui-input"
                  value={draft}
                  maxLength={120}
                  aria-label="Nuevo título"
                  autoFocus
                  onChange={(event) => setDraft(event.target.value)}
                />
                <button type="submit" className="ui-button ui-button--compact">
                  Guardar
                </button>
              </ValidatedForm>
            ) : (
              <>
                <button
                  type="button"
                  className="copilot-history__open"
                  onClick={() => onOpen(item.id)}
                >
                  <strong>{item.title}</strong>
                  <span>
                    {item.interaction_mode === "work" ? "Encargo" : "Pregunta"} ·{" "}
                    {relativeDay(item.last_activity_at)}
                  </span>
                </button>
                <span className="copilot-history__actions">
                  <button
                    type="button"
                    className="ui-icon-button copilot__icon"
                    aria-label={`Renombrar ${item.title}`}
                    onClick={() => {
                      setRenaming(item.id);
                      setDraft(item.title);
                    }}
                  >
                    <Icon name="edit" size={16} />
                  </button>
                  <button
                    type="button"
                    className="ui-button ui-button--ghost ui-button--compact"
                    onClick={() => void update(item.id, { archived: !item.archived })}
                  >
                    {item.archived ? "Desarchivar" : "Archivar"}
                  </button>
                </span>
              </>
            )}
          </li>
        ))}
      </ul>
      {cursor ? (
        <button type="button" className="ask-dock__meta-link" onClick={() => void load(cursor)}>
          Cargar más
        </button>
      ) : null}
    </nav>
  );
}
