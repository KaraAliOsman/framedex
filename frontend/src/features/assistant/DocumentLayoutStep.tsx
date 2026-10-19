import { useState } from "react";
import { Link } from "react-router-dom";

import { quotationLayoutGet, quotationLayoutSave } from "../../api/generated/dekopen";
import type { AiAgentStep, QuotationLayout } from "../../api/generated/models";
import { Icon } from "../../ui/Icon";
import { actionErrorDetail } from "../errors";
import "./operations.css";

const TEMPLATE: Record<string, string> = {
  ESENCIAL: "Esencial",
  PROYECTO: "Proyecto",
  ALTERNATIVAS: "Alternativas",
};
const SIZE: Record<string, string> = { S: "pequeños", M: "medianos", L: "grandes" };

/** Human summary of a composition change; never a number of the quotation. */
function describe(layout: QuotationLayout): string[] {
  const lines: string[] = [];
  if (layout.template) lines.push(`Diseño ${TEMPLATE[layout.template] ?? layout.template}`);
  if (layout.order) lines.push("Nuevo orden de bloques");
  if (layout.hidden)
    lines.push(layout.hidden.length ? "Bloques ocultos ajustados" : "Todos los bloques visibles");
  if (layout.texts?.intro !== undefined) lines.push("Texto de presentación");
  if (layout.texts?.notes !== undefined) lines.push("Notas en condiciones");
  if (layout.texts?.closing !== undefined) lines.push("Texto de cierre");
  if (layout.drawing_size)
    lines.push(`Dibujos ${SIZE[layout.drawing_size] ?? layout.drawing_size}`);
  if (layout.unit_prices !== undefined)
    lines.push(layout.unit_prices ? "Muestra precio unitario" : "Oculta precio unitario");
  return lines;
}

export const QUOTATION_LAYOUT_EVENT = "dekopen:quotation-layout";

/** The assistant changed (or proposes) the same composition the document
 * editor edits; the receipt applies or undoes it with the same save. */
export function DocumentLayoutStep({
  step,
  organizationId,
  declined = false,
  onSettled,
}: {
  step: AiAgentStep;
  organizationId: string;
  declined?: boolean;
  onSettled(action: "applied" | "declined" | "apply_failed" | "undone"): void;
}): JSX.Element {
  const applied = step.applied as { previous?: QuotationLayout } | undefined;
  const [state, setState] = useState<"proposed" | "applied" | "undone" | "declined">(
    applied ? "applied" : declined ? "declined" : "proposed",
  );
  const [previous, setPrevious] = useState<QuotationLayout | undefined>(applied?.previous);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState(step.apply_error ?? "");
  const projectId = step.project_id ?? "";
  const layout = (step.layout ?? {}) as QuotationLayout;
  const headers = { headers: { "X-Organization-ID": organizationId } };

  function announce(): void {
    window.dispatchEvent(new CustomEvent(QUOTATION_LAYOUT_EVENT, { detail: { projectId } }));
  }

  async function apply(): Promise<void> {
    setBusy(true);
    setMessage("");
    try {
      const current = await quotationLayoutGet(projectId, headers);
      if (current.status !== 200) throw new Error("read");
      const saved = await quotationLayoutSave(
        projectId,
        { ...current.data.layout, ...layout },
        headers,
      );
      if (saved.status !== 200) throw new Error("save");
      setPrevious(current.data.layout);
      setState("applied");
      onSettled("applied");
      announce();
    } catch (error) {
      setMessage(actionErrorDetail(error, "No se pudo cambiar el documento. Vuelve a intentar."));
      onSettled("apply_failed");
    } finally {
      setBusy(false);
    }
  }

  async function undo(): Promise<void> {
    if (!previous) return;
    setBusy(true);
    setMessage("");
    try {
      const saved = await quotationLayoutSave(projectId, previous, headers);
      if (saved.status !== 200) throw new Error("save");
      setState("undone");
      onSettled("undone");
      announce();
    } catch (error) {
      setMessage(actionErrorDetail(error, "No se pudo deshacer. Vuelve a intentar."));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section
      className="ask-dock__ops operation-project"
      data-state={state}
      aria-label={state === "applied" ? "Documento cambiado" : "Propuesta para el documento"}
    >
      <p className="operation-project__label">
        {state === "applied" ? <Icon name="check" size={16} /> : <Icon name="document" size={16} />}
        {step.label}
      </p>
      <ul className="operation-project__changes">
        {describe(layout).map((line) => (
          <li key={line}>{line}</li>
        ))}
      </ul>
      {message ? <p role="alert">{message}</p> : null}
      <div className="ask-dock__ops-actions">
        {state === "proposed" ? (
          <>
            <button
              type="button"
              className="ask-dock__action ask-dock__action--primary"
              disabled={busy || !projectId}
              onClick={() => void apply()}
            >
              Aplicar
            </button>
            <button
              type="button"
              className="ask-dock__action ask-dock__action--ghost"
              disabled={busy}
              onClick={() => {
                setState("declined");
                onSettled("declined");
              }}
            >
              Descartar
            </button>
          </>
        ) : null}
        {state === "applied" && previous ? (
          <button
            type="button"
            className="ask-dock__action ask-dock__action--ghost"
            disabled={busy}
            onClick={() => void undo()}
          >
            Deshacer
          </button>
        ) : null}
        {projectId ? (
          <Link
            className="ask-dock__action ask-dock__action--ghost"
            to={`/projects/${projectId}?section=quote`}
          >
            Ver documento
          </Link>
        ) : null}
      </div>
      {state === "undone" ? (
        <p>Cambio deshecho. El documento volvió a su diseño anterior.</p>
      ) : null}
      {state === "declined" ? <p>Propuesta descartada.</p> : null}
    </section>
  );
}
