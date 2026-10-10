import { useState } from "react";
import type { ApprovalRecord, ProjectResponse } from "../../api/generated/models";
import { formatDateTime, formatRevision } from "../../format";
import { StatusBadge } from "../../ui/StatusBadge";

const labels: Record<string, string> = {
  ACTIVE: "Vigente",
  VIEWED: "Visto",
  SUPERSEDED: "Reemplazado",
  EXPIRED: "Vencido",
  REVOKED: "Revocado",
  APPROVED: "Aprobado",
  DECLINED: "Cambios solicitados",
};

function Deadline({
  busy,
  onChange,
}: {
  busy: boolean;
  onChange: (date: string) => void;
}): JSX.Element {
  const [date, setDate] = useState("");
  return (
    <details className="quotation-deadline">
      <summary>Cambiar vencimiento</summary>
      <label>
        Nuevo vencimiento del enlace
        <input
          type="datetime-local"
          value={date}
          onChange={(event) => setDate(event.target.value)}
          disabled={busy}
        />
      </label>
      <p>Hora local del navegador. La vigencia comercial conserva la fecha sellada del PDF.</p>
      <button
        type="button"
        disabled={!date || busy}
        onClick={() => onChange(new Date(date).toISOString())}
      >
        Revisar vencimiento
      </button>
    </details>
  );
}

export function QuotationLinkLedger({
  project,
  links,
  canWrite,
  busy,
  onRevoke,
  onRegenerate,
  onDeadline,
}: {
  project: ProjectResponse;
  links: ApprovalRecord[];
  canWrite: boolean;
  busy: boolean;
  onRevoke: (id: string) => void;
  onRegenerate: (link: ApprovalRecord) => void;
  onDeadline: (link: ApprovalRecord, date: string) => void;
}): JSX.Element {
  return (
    <section className="quotation-links" aria-label="Historial del enlace">
      <h3>Historial del enlace</h3>
      {links.length === 0 ? (
        <p>Aún no se ha emitido un enlace. Se activará al emitir y enviar la cotización.</p>
      ) : (
        <ol className="quotation-link-timeline">
          {links.map((link) => {
            const state =
              link.link_state ??
              (link.revision_code !== project.current_revision
                ? "SUPERSEDED"
                : link.status === "REVOKED"
                  ? "REVOKED"
                  : Date.parse(link.expires_at) <= Date.now()
                    ? "EXPIRED"
                    : link.status !== "PENDING"
                      ? link.status
                      : link.view_count
                        ? "VIEWED"
                        : "ACTIVE");
            const current = link.revision_code === project.current_revision;
            const controls =
              current && canWrite && (link.status === "PENDING" || link.status === "REVOKED");
            return (
              <li className="quotation-link" key={link.id}>
                <div className="quotation-link__title">
                  <strong>{formatRevision(link.revision_code)}</strong>
                  <StatusBadge showIcon={false} data-status={state.toLowerCase()}>
                    {labels[state] ?? "Sin dato"}
                  </StatusBadge>
                  <span>
                    {link.link_source === "DOCUMENT" ? "QR del PDF" : "Enlace regenerado"}
                  </span>
                </div>
                <ol className="quotation-link-events">
                  <li>
                    Emitido ·{" "}
                    <time dateTime={link.created_at}>{formatDateTime(link.created_at)}</time>
                  </li>
                  <li>
                    Acceso hasta ·{" "}
                    <time dateTime={link.expires_at}>{formatDateTime(link.expires_at)}</time>
                  </li>
                  {link.last_viewed_at ? (
                    <li>
                      Visto {link.view_count} {link.view_count === 1 ? "vez" : "veces"} ·{" "}
                      {formatDateTime(link.last_viewed_at)}
                    </li>
                  ) : null}
                  {link.decided_at ? (
                    <li>
                      {link.status === "DECLINED" ? "Cambios solicitados" : "Aprobado"} por{" "}
                      {link.decided_by} · {formatDateTime(link.decided_at)}
                      {link.decided_note ? <blockquote>{link.decided_note}</blockquote> : null}
                    </li>
                  ) : null}
                  {link.revoked_at ? <li>Revocado · {formatDateTime(link.revoked_at)}</li> : null}
                  {!current ? (
                    <li>
                      Reemplazado por {formatRevision(project.current_revision)}. Se conserva la
                      decisión anterior.
                    </li>
                  ) : null}
                </ol>
                {controls ? (
                  <div className="quotation-link-controls">
                    {link.status === "PENDING" ? (
                      <button type="button" disabled={busy} onClick={() => onRevoke(link.id)}>
                        Revocar enlace
                      </button>
                    ) : null}
                    <button type="button" disabled={busy} onClick={() => onRegenerate(link)}>
                      Regenerar enlace
                    </button>
                    {link.status === "PENDING" ? (
                      <Deadline busy={busy} onChange={(date) => onDeadline(link, date)} />
                    ) : null}
                  </div>
                ) : null}
              </li>
            );
          })}
        </ol>
      )}
    </section>
  );
}
