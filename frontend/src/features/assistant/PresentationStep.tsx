import { lazy, Suspense, useEffect, useMemo, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { ApiError } from "../../api/apiMutator";
import {
  aiPresentationApply,
  aiPresentationPreview,
  aiPresentationState,
  aiPresentationUndo,
} from "../../api/generated/dekopen";
import type {
  AiAgentStep,
  PresentationPreviewResponse,
  PresentationPatch,
} from "../../api/generated/models";

const RealDocumentPreview = lazy(() =>
  import("../settings/AdminSections").then((module) => ({ default: module.DocumentPreview })),
);

function detail(error: unknown): string {
  if (error instanceof ApiError) {
    const text = (error.payload as { error?: { detail?: string } })?.error?.detail;
    if (text) return text;
    if (error.status === 403)
      return "Solo el dueño puede aplicar cambios de presentación. Comprueba tu sesión y la verificación de seguridad.";
  }
  return "No pudimos completar el cambio. Tu propuesta sigue aquí para reintentarlo.";
}

export function PresentationStep({
  step,
  organizationId,
  operationKey,
  declined = false,
  onSettled,
}: {
  step: AiAgentStep;
  organizationId: string;
  operationKey: string;
  declined?: boolean;
  onSettled(
    action: "applied" | "declined" | "apply_failed" | "undone",
    ops: { op?: string }[],
  ): void;
}): JSX.Element {
  const queryClient = useQueryClient();
  const initial = step.simulation as PresentationPreviewResponse | undefined;
  const [preview, setPreview] = useState(initial ?? null);
  const [state, setState] = useState("PROPOSED");
  const [operationId, setOperationId] = useState<string | null>(null);
  const [busy, setBusy] = useState(true);
  const [message, setMessage] = useState("");
  const [attempt, setAttempt] = useState(0);
  const [showDocument, setShowDocument] = useState(false);
  const documentDraft = useMemo(
    () => ({ document_preferences: preview?.patch ?? {} }),
    [preview?.patch],
  );
  const patchKey = JSON.stringify(initial?.patch ?? {});
  useEffect(() => {
    let active = true;
    const options = { headers: { "X-Organization-ID": organizationId } };
    setBusy(true);
    void (async () => {
      const saved = await aiPresentationState({ operation_key: operationKey }, options);
      if (saved.status !== 200) throw new ApiError(saved.status, saved.data);
      if (!active) return;
      setState(saved.data.state);
      setOperationId(saved.data.operation_id);
      if (attempt > 0 && saved.data.state === "PROPOSED") {
        const response = await aiPresentationPreview(
          { patch: JSON.parse(patchKey) as PresentationPatch },
          options,
        );
        if (response.status !== 200) throw new ApiError(response.status, response.data);
        if (active) setPreview(response.data);
      }
    })()
      .catch((error: unknown) => {
        if (active) setMessage(detail(error));
      })
      .finally(() => {
        if (active) setBusy(false);
      });
    return () => {
      active = false;
    };
  }, [organizationId, operationKey, patchKey, attempt]);

  async function apply(undo = false): Promise<void> {
    if (busy || !preview) return;
    setBusy(true);
    setMessage("");
    try {
      const options = { headers: { "X-Organization-ID": organizationId } };
      const result =
        undo && operationId
          ? await aiPresentationUndo(operationId, options)
          : await aiPresentationApply(
              { patch: preview.patch, before_sig: preview.before_sig, operation_key: operationKey },
              options,
            );
      if (result.status !== 200) throw new ApiError(result.status, result.data);
      setOperationId(result.data.operation_id);
      setState(undo ? "UNDONE" : "APPLIED");
      onSettled(undo ? "undone" : "applied", [{ op: "presentation" }]);
      void queryClient.invalidateQueries();
    } catch (error) {
      setMessage(detail(error));
      if (!undo) onSettled("apply_failed", [{ op: "presentation" }]);
    } finally {
      setBusy(false);
    }
  }
  const after = (preview?.after ?? {}) as Record<string, string>;
  return (
    <section className="ask-dock__ops" aria-label="Propuesta de presentación">
      <strong>{step.label || "Presentación de tu empresa"}</strong>
      {preview ? (
        <>
          <div
            className={`presentation-sample presentation-sample--${after.accent?.toLowerCase() ?? "teal"}`}
          >
            <span className="presentation-sample__label">
              Muestra de estilo · {after.quotation_layout === "COMPACT" ? "Compacto" : "Editorial"}{" "}
              · {after.paper}
            </span>
            <h3>{after.presentation_title || "Propuesta para su obra"}</h3>
            {after.presentation_intro ? <p>{after.presentation_intro}</p> : null}
            {preview.patch.portal_heading !== undefined ||
            preview.patch.portal_intro !== undefined ? (
              <div className="presentation-sample__portal">
                <span>Página del cliente</span>
                <h3>{after.portal_heading || "Su obra"}</h3>
                <p>{after.portal_intro}</p>
              </div>
            ) : null}
          </div>
          <details>
            <summary>{preview.changes.length} cambios de presentación</summary>
            <ul>
              {preview.changes.map((change, index) => (
                <li key={index}>
                  <strong>{String(change.label)}</strong>
                  <p>{String(change.after || "Sin texto adicional")}</p>
                </li>
              ))}
            </ul>
          </details>
          <p className="ask-dock__hint">{preview.scope}</p>
          <details onToggle={(event) => setShowDocument(event.currentTarget.open)}>
            <summary>Ver un PDF con estos cambios</summary>
            {showDocument ? (
              <Suspense fallback={<p role="status">Preparando la vista del documento…</p>}>
                <RealDocumentPreview orgId={organizationId} branding={documentDraft} />
              </Suspense>
            ) : null}
          </details>
        </>
      ) : (
        <p>No hay una muestra disponible. Pide una nueva propuesta.</p>
      )}
      {message ? (
        <p role="alert">
          {message}{" "}
          <button
            type="button"
            className="ask-dock__meta-link"
            disabled={busy}
            onClick={() => {
              setMessage("");
              setAttempt((value) => value + 1);
            }}
          >
            Actualizar muestra
          </button>
        </p>
      ) : null}
      {state === "APPLIED" ? (
        <p role="status">
          Presentación guardada.{" "}
          <button
            type="button"
            className="ask-dock__action"
            disabled={busy}
            onClick={() => void apply(true)}
          >
            Deshacer
          </button>
        </p>
      ) : state === "UNDONE" ? (
        <p role="status">Cambio deshecho.</p>
      ) : declined || state === "DECLINED" ? (
        <p>Propuesta descartada.</p>
      ) : (
        <div className="ask-dock__ops-actions">
          <button
            type="button"
            className="ask-dock__action"
            disabled={busy || !preview?.valid || !preview.changes.length || !!message}
            onClick={() => void apply()}
          >
            Aplicar presentación
          </button>
          <button
            type="button"
            className="ask-dock__action ask-dock__action--ghost"
            disabled={busy}
            onClick={() => {
              setState("DECLINED");
              onSettled("declined", [{ op: "presentation" }]);
            }}
          >
            Descartar
          </button>
        </div>
      )}
    </section>
  );
}
