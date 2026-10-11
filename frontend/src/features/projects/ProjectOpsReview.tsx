import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import {
  projectOperationsPreview,
  projectOperationsApply,
  projectOperationsUndo,
} from "../../api/generated/dekopen";
import type {
  DesignOperationRequest,
  ProjectOpsPreviewResponse,
  ProjectResponse,
} from "../../api/generated/models";
import { ApiError } from "../../api/apiMutator";
import { fmtMm, formatMoney } from "../../format";
import { DimLoader } from "../../ui";
import { actionErrorDetail } from "../errors";
import { SimulationPreview } from "../assistant/SimulationPreview";

export function useProjectOperations(
  project: ProjectResponse,
  orgId: string,
  onChanged: () => Promise<unknown>,
) {
  const [proposal, setProposal] = useState<{
    title: string;
    ops: DesignOperationRequest[];
    preview: ProjectOpsPreviewResponse;
    key: string;
  } | null>(null);
  const [undoId, setUndoId] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const lock = useRef(false);
  const lifetime = useRef<AbortController | null>(null);
  useEffect(() => {
    const controller = new AbortController();
    lifetime.current = controller;
    return () => controller.abort();
  }, [project.id, orgId]);
  const options = () => ({
    signal: lifetime.current?.signal,
    headers: { "X-Organization-ID": orgId },
  });
  async function propose(ops: DesignOperationRequest[], title: string): Promise<boolean> {
    if (lock.current || !lifetime.current || lifetime.current.signal.aborted) return false;
    const controller = lifetime.current;
    lock.current = true;
    setBusy(true);
    setError("");
    setNotice("");
    setProposal(null);
    try {
      const result = await projectOperationsPreview(project.id, { ops }, options());
      if (result.status !== 200) throw new ApiError(result.status, result.data);
      if (controller.signal.aborted) return false;
      setProposal({ ops, title, preview: result.data, key: crypto.randomUUID() });
      return true;
    } catch (cause) {
      if (!controller.signal.aborted)
        setError(
          actionErrorDetail(
            cause,
            "El motor no pudo preparar el cambio. Revisa las posiciones y vuelve a intentar.",
          ),
        );
      return false;
    } finally {
      lock.current = false;
      if (!controller.signal.aborted) setBusy(false);
    }
  }
  async function apply(): Promise<void> {
    if (!proposal || lock.current || !lifetime.current || lifetime.current.signal.aborted) return;
    const controller = lifetime.current;
    lock.current = true;
    setBusy(true);
    setError("");
    try {
      const result = await projectOperationsApply(
        project.id,
        { ops: proposal.ops, before_sig: proposal.preview.before_sig, operation_key: proposal.key },
        options(),
      );
      if (result.status !== 200) throw new ApiError(result.status, result.data);
      if (controller.signal.aborted) return;
      setUndoId(result.data.operation_id);
      setProposal(null);
      setNotice(
        "Cambio aplicado. El precio de la propuesta es indicativo; calcula y aplica el precio antes de emitir.",
      );
      await onChanged();
    } catch (cause) {
      if (!controller.signal.aborted)
        setError(
          actionErrorDetail(
            cause,
            "No se pudo confirmar el cambio. Puedes reintentar la misma propuesta sin duplicarla.",
          ),
        );
    } finally {
      lock.current = false;
      if (!controller.signal.aborted) setBusy(false);
    }
  }
  async function undo(): Promise<void> {
    if (!undoId || lock.current || !lifetime.current || lifetime.current.signal.aborted) return;
    const controller = lifetime.current;
    lock.current = true;
    setBusy(true);
    setError("");
    try {
      const result = await projectOperationsUndo(project.id, undoId, options());
      if (result.status !== 200) throw new ApiError(result.status, result.data);
      if (controller.signal.aborted) return;
      setUndoId("");
      setNotice("Cambio deshecho. Se restauraron posiciones, orden y preparación anteriores.");
      await onChanged();
    } catch (cause) {
      if (!controller.signal.aborted)
        setError(
          actionErrorDetail(
            cause,
            "No se pudo deshacer. Revisa si alguien guardó una edición posterior.",
          ),
        );
    } finally {
      lock.current = false;
      if (!controller.signal.aborted) setBusy(false);
    }
  }
  return {
    proposal,
    busy,
    error,
    notice,
    undoId,
    propose,
    apply,
    undo,
    cancel: () => setProposal(null),
  };
}

type Change = {
  kind: string;
  index: number;
  before: Record<string, unknown> | null;
  after: Record<string, unknown> | null;
};
function description(row: Record<string, unknown> | null): string {
  if (!row) return "Sin posición";
  const place = row.placement as Record<string, string> | undefined;
  const design = row.design as
    { nominal_width_mm?: string; nominal_height_mm?: string } | undefined;
  const dimensions =
    design?.nominal_width_mm && design.nominal_height_mm
      ? `${fmtMm(design.nominal_width_mm)} × ${fmtMm(design.nominal_height_mm)} mm`
      : "Medidas sin dato · abre el editor";
  return `${row.location_tag || "Sin ubicación"} · ${dimensions} · cantidad ${row.quantity}${
    place
      ? Object.values(place)
          .filter(Boolean)
          .map((value) => ` · ${value}`)
          .join("")
      : ""
  } · orden ${row.display_order ?? row.position_index}`;
}
export function ProjectOpsReview({
  operations,
  orgId,
  currency,
}: {
  operations: ReturnType<typeof useProjectOperations>;
  orgId: string;
  currency: string;
}): JSX.Element {
  const { proposal } = operations;
  return (
    <div className="project-ops-review" aria-live="polite">
      {operations.busy && <DimLoader label="Revisando el cambio con el motor" />}
      {operations.error && <p role="alert">{operations.error}</p>}
      {operations.notice && <p role="status">{operations.notice}</p>}
      {operations.undoId && (
        <button type="button" disabled={operations.busy} onClick={() => void operations.undo()}>
          Deshacer último cambio
        </button>
      )}
      {proposal && (
        <section aria-label="Revisar cambios antes de aplicar">
          <h3>{proposal.title}</h3>
          <p>
            {proposal.preview.diff.length} posiciones afectadas. Revisa el antes y después; la
            propuesta todavía no se ha aplicado.
          </p>
          <p>
            Δ de Uw: Sin dato · faltan autoridades térmicas de perfiles, vidrio y separador.{" "}
            <Link to="/catalog">Revisar fuentes del catálogo</Link>
          </p>
          <ol className="project-ops-diff">
            {proposal.preview.diff.map((raw, index) => {
              const change = raw as Change;
              const simulation = proposal.preview.simulations[index] as {
                price?: { delta_net?: string | null; currency?: string; reason?: string };
              };
              return (
                <li key={String(change.after?.id ?? change.before?.id)}>
                  <strong>
                    Posición {change.index} ·{" "}
                    {change.kind === "add"
                      ? "Agregar"
                      : change.kind === "remove"
                        ? "Eliminar"
                        : "Cambiar"}
                  </strong>
                  <span className="project-number">
                    {description(change.before)} → {description(change.after)}
                  </span>
                  <span className="project-number">
                    Δ neto{" "}
                    {simulation?.price?.delta_net != null
                      ? formatMoney(
                          simulation.price.delta_net,
                          simulation.price.currency ?? currency,
                        )
                      : `Sin dato · ${simulation?.price?.reason ?? "calcula el precio del proyecto"}`}
                  </span>
                  <details>
                    <summary>Dibujo y fuente del motor</summary>
                    <SimulationPreview
                      simulation={proposal.preview.simulations[index]}
                      organizationId={orgId}
                    />
                  </details>
                </li>
              );
            })}
          </ol>
          <div className="projects-actions">
            <button
              type="button"
              className="primary-action"
              disabled={operations.busy || !proposal.preview.diff.length}
              onClick={() => void operations.apply()}
            >
              Aplicar cambios revisados
            </button>
            <button type="button" disabled={operations.busy} onClick={operations.cancel}>
              Descartar propuesta
            </button>
          </div>
        </section>
      )}
    </div>
  );
}
