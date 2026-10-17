import { useEffect, useRef, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { Icon } from "../../ui/Icon";
import { AgentBody, SURFACE_LABELS } from "./AgentBody";
import { stableRefs, useAssistantContext } from "./assistantContext";
import { useAssistantPresence } from "./useAssistantPresence";
import { Orb } from "./Orb";
import "./assistant.css";
import "./assistant-room.css";

/** One contextual conversation for questions and complete delegated work. */
export function AskDekopen({
  organizationId,
  userId = null,
  openRequested = 0,
  hideTrigger = false,
}: {
  organizationId: string | null;
  userId?: string | null;
  openRequested?: number;
  hideTrigger?: boolean;
}): JSX.Element | null {
  const { surface, refs } = useAssistantContext();
  const location = useLocation();
  const presence = useAssistantPresence({ organizationId, userId, surface, refs });
  const [open, setOpen] = useState(() => sessionStorage.getItem("dk:askdock") === "1");
  const [composing, setComposing] = useState(false);
  const [composedText, setComposedText] = useState("");
  const [draft, setDraft] = useState<{ text: string; request: number } | null>(null);
  const previousFocus = useRef<HTMLElement | null>(null);
  const requestedJob = new URLSearchParams(location.search).get("assistant_job");
  useEffect(() => {
    if (requestedJob) setOpen(true);
  }, [requestedJob]);
  useEffect(() => {
    if (location.pathname.startsWith("/assistant")) setOpen(false);
  }, [location.pathname]);
  useEffect(() => {
    if (!open) return;
    previousFocus.current = document.activeElement as HTMLElement | null;
    return () => {
      previousFocus.current?.focus();
    };
  }, [open]);
  useEffect(() => {
    sessionStorage.setItem("dk:askdock", open ? "1" : "0");
  }, [open]);
  useEffect(() => {
    if (openRequested > 0) setOpen(true);
  }, [openRequested]);
  useEffect(() => {
    const show = (event: Event) => {
      const detail = (event as CustomEvent<{ prompt?: string }>).detail;
      setDraft((current) => ({ text: detail?.prompt ?? "", request: (current?.request ?? 0) + 1 }));
      setOpen(true);
    };
    window.addEventListener("dekopen:assistant", show);
    return () => window.removeEventListener("dekopen:assistant", show);
  }, []);
  if (!organizationId) return null;
  return (
    <div
      className={`ask-dock${open ? " ask-dock--open" : ""}${surface === "position" ? " ask-dock--canvas" : ""}`}
    >
      {open ? (
        <section
          className="ask-dock__panel"
          aria-label="Asistente DEKOPEN"
          onKeyDown={(event) => {
            if (event.key === "Escape") setOpen(false);
          }}
        >
          <header className="ask-dock__header">
            <Orb state={composing ? "input" : presence.orbState} size={28} />
            <span className="ask-dock__title">
              DEKOPEN IA<small>Trabajamos sobre lo que estás viendo</small>
            </span>
            <Link
              className="ui-icon-button"
              state={{ assistantDraft: composedText }}
              to={
                presence.job
                  ? `/assistant?job=${presence.job.id}`
                  : `/assistant${refs.project_id ? `?project=${refs.project_id}` : ""}`
              }
              onClick={() => setOpen(false)}
              aria-label="Abrir conversación completa"
              title="Abrir conversación completa"
            >
              <Icon name="expand" size={17} />
            </Link>
            <button
              type="button"
              className="ask-dock__close"
              onClick={() => setOpen(false)}
              aria-label="Cerrar asistente"
            >
              <Icon name="close" size={20} />
            </button>
          </header>
          <p className="ask-dock__context">
            <Icon name={surface === "position" ? "window" : "projects"} size={16} />
            {presence.data?.context_label ?? SURFACE_LABELS[surface] ?? "Tu trabajo"}
          </p>
          <AgentBody
            key={`${organizationId}:${userId}:${surface}:${JSON.stringify(stableRefs(refs))}`}
            organizationId={organizationId}
            userId={userId}
            surface={surface}
            refs={refs}
            jobId={requestedJob}
            onComposing={setComposing}
            onDraftChange={setComposedText}
            draft={draft}
          />
        </section>
      ) : hideTrigger ? null : (
        <button
          type="button"
          className="ask-dock__trigger"
          onClick={() => setOpen(true)}
          aria-label="Abrir asistente"
        >
          <Orb state={presence.orbState} size={28} />
        </button>
      )}
    </div>
  );
}
