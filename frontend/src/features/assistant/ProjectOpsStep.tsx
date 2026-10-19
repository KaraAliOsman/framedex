import { useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { ApiError } from "../../api/apiMutator";
import {
  projectOperationsApply,
  projectOperationsPreview,
  projectOperationsState,
  projectOperationsUndo,
} from "../../api/generated/dekopen";
import type {
  AiAgentStep,
  DesignOperationRequest,
  ProjectOpsPreviewResponse,
} from "../../api/generated/models";
import { fmtMm } from "../../format";
import { Loading } from "../../ui/Signature";
import { SimulationPreview } from "./SimulationPreview";
import { Link } from "react-router-dom";
import { Icon } from "../../ui/Icon";
import "./operations.css";

type Position = {
  id?: string;
  position_index: number;
  location_tag?: string;
  quantity: number;
  design?: { nominal_width_mm: string; nominal_height_mm: string };
};
type Change = { kind: string; index: number; before?: Position | null; after?: Position | null };

/** Effects are server responses. Requests contain only the registered intent. */
export function operationIntent(op: Record<string, unknown>): DesignOperationRequest {
  return Object.fromEntries(
    Object.entries(op).filter(
      ([key]) => !["base_sig", "result", "description", "context_effect"].includes(key),
    ),
  ) as unknown as DesignOperationRequest;
}

function summary(position: Position | null | undefined): string {
  if (!position) return "Sin ventana";
  const design = position.design;
  const units = Number(position.quantity) === 1 ? "1 unidad" : `${position.quantity} unidades`;
  return `${position.location_tag || `Ventana ${position.position_index}`} · ${units}${design ? ` · ${fmtMm(design.nominal_width_mm)} × ${fmtMm(design.nominal_height_mm)} mm` : ""}`;
}

export function ProjectOpsStep({
  step,
  organizationId,
  projectId,
  operationKey,
  declined = false,
  linkToProject = false,
  onSettled,
}: {
  step: AiAgentStep;
  organizationId: string;
  projectId: string;
  operationKey: string;
  declined?: boolean;
  /** The assistant worked on a different work than the current page. */
  linkToProject?: boolean;
  onSettled(
    action: "applied" | "declined" | "apply_failed" | "undone",
    ops: { op?: string }[],
  ): void;
}): JSX.Element {
  const queryClient = useQueryClient();
  const [preview, setPreview] = useState<ProjectOpsPreviewResponse | null>(null);
  const [busy, setBusy] = useState(true);
  const [message, setMessage] = useState("");
  const [operationId, setOperationId] = useState<string | null>(null);
  const [state, setState] = useState<"proposed" | "applied" | "undone" | "declined">("proposed");
  const [attempt, setAttempt] = useState(0);
  const ops = (step.ops ?? []).map((op) =>
    operationIntent(op as unknown as Record<string, unknown>),
  );
  const key = JSON.stringify(ops);
  useEffect(() => {
    let active = true;
    setBusy(true);
    setMessage("");
    setPreview(null);
    void (async () => {
      const headers = { headers: { "X-Organization-ID": organizationId } };
      const saved = await projectOperationsState(
        projectId,
        { operation_key: operationKey },
        headers,
      );
      if (saved.status !== 200) throw new ApiError(saved.status, saved.data);
      if (!active) return;
      setOperationId(saved.data.operation_id);
      setState(
        saved.data.state === "APPLIED"
          ? "applied"
          : saved.data.state === "UNDONE"
            ? "undone"
            : declined
              ? "declined"
              : "proposed",
      );
      const initial = step.simulation as ProjectOpsPreviewResponse | undefined;
      if (
        initial?.valid &&
        initial.project_id === projectId &&
        initial.before_sig &&
        (attempt === 0 || saved.data.state !== "PROPOSED")
      ) {
        setPreview(initial);
        return;
      }
      const response = await projectOperationsPreview(
        projectId,
        { ops: JSON.parse(key) as DesignOperationRequest[] },
        headers,
      );
      if (response.status !== 200) throw new ApiError(response.status, response.data);
      if (active) setPreview(response.data);
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
  }, [projectId, organizationId, key, step.simulation, operationKey, declined, attempt]);

  function detail(error: unknown): string {
    if (error instanceof ApiError && error.status === 403) {
      return "No tienes permiso para cambiar este proyecto. Solo el dueño o un estimador puede hacerlo; pídele que revise la propuesta.";
    }
    if (error instanceof ApiError && error.payload && typeof error.payload === "object") {
      const value = (error.payload as { error?: { detail?: string } }).error?.detail;
      if (value) return value;
    }
    return "No pudimos completar el cambio. Revisa el proyecto y vuelve a simular la propuesta.";
  }

  async function apply(): Promise<void> {
    if (!preview || busy) return;
    setBusy(true);
    setMessage("");
    try {
      const response = await projectOperationsApply(
        projectId,
        { ops, before_sig: preview.before_sig, operation_key: operationKey },
        { headers: { "X-Organization-ID": organizationId } },
      );
      if (response.status !== 200) throw new ApiError(response.status, response.data);
      setOperationId(response.data.operation_id);
      setState(response.data.state === "UNDONE" ? "undone" : "applied");
      onSettled("applied", ops);
      void queryClient.invalidateQueries();
    } catch (error) {
      setMessage(detail(error));
      onSettled("apply_failed", ops);
    } finally {
      setBusy(false);
    }
  }

  async function undo(): Promise<void> {
    if (!operationId || busy) return;
    setBusy(true);
    setMessage("");
    try {
      const response = await projectOperationsUndo(projectId, operationId, {
        headers: { "X-Organization-ID": organizationId },
      });
      if (response.status !== 200) throw new ApiError(response.status, response.data);
      setState("undone");
      onSettled("undone", ops);
      void queryClient.invalidateQueries();
    } catch (error) {
      setMessage(detail(error));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section
      className="ask-dock__ops operation-project"
      data-state={state}
      aria-label={state === "applied" ? "Cambios guardados en la obra" : "Propuesta para la obra"}
    >
      <p className="operation-project__label">
        {state === "applied" ? <Icon name="check" size={16} /> : null}
        {step.label}
      </p>
      {busy ? (
        <Loading label={state === "proposed" ? "Calculando la propuesta" : "Guardando"} />
      ) : null}
      {message ? (
        <div>
          <p role="alert">{message}</p>
          <button
            type="button"
            className="ask-dock__action ask-dock__action--ghost"
            disabled={busy}
            onClick={() => setAttempt((value) => value + 1)}
          >
            Reintentar simulación
          </button>
        </div>
      ) : null}
      {preview ? (
        <ul className="operation-project__changes">
          {(preview.diff as Change[]).map((change, index) => (
            <li key={index}>
              <strong>
                {change.kind === "add" ? "Nueva" : change.kind === "remove" ? "Quitar" : "Cambia"} ·
                ventana {change.index}
              </strong>
              {change.before ? <p>Antes: {summary(change.before)}</p> : null}
              {change.after ? (
                <p>
                  {state === "applied" ? "Ahora" : "Queda"}: {summary(change.after)}
                </p>
              ) : null}
              {preview.simulations
                .filter(
                  (simulation) =>
                    (simulation as { position_id?: string }).position_id ===
                    (change.after ?? change.before)?.id,
                )
                .map((simulation, index) => (
                  <SimulationPreview
                    key={index}
                    simulation={simulation}
                    organizationId={organizationId}
                  />
                ))}
            </li>
          ))}
        </ul>
      ) : null}
      {preview && !preview.diff.length ? (
        <p>La propuesta coincide con el proyecto. No hay cambios que aplicar.</p>
      ) : null}
      {preview && !preview.valid ? (
        <p role="alert">
          El proyecto bloquea esta propuesta. Revisa las posiciones y vuelve a simular.
        </p>
      ) : null}
      {state === "proposed" ? (
        <div className="ask-dock__ops-actions">
          <button
            type="button"
            className="ask-dock__action ask-dock__action--primary"
            disabled={busy || !preview?.valid || !preview.diff.length}
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
              onSettled("declined", ops);
            }}
          >
            Descartar
          </button>
        </div>
      ) : (
        <div className="operation-project__receipt" role="status">
          <span>
            {state === "applied"
              ? "Guardado en la obra"
              : state === "undone"
                ? "Deshecho"
                : "Propuesta descartada"}
          </span>
          {state === "applied" ? (
            <button
              type="button"
              className="ask-dock__action"
              disabled={busy}
              onClick={() => void undo()}
            >
              <Icon name="undo" size={16} />
              Deshacer
            </button>
          ) : null}
          {linkToProject && state !== "declined" ? (
            <Link className="ask-dock__action" to={`/projects/${projectId}`}>
              Abrir obra
            </Link>
          ) : null}
        </div>
      )}
    </section>
  );
}
